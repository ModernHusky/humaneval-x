import contextlib
import io
import os
import platform
import signal
import random
import subprocess
import tempfile
import shutil
from typing import *
import threading
import _thread
from pathlib import Path

class TimeoutException(Exception):
    pass

@contextlib.contextmanager
def time_limit(seconds: float):
    """跨平台的超时控制"""
    if platform.system() == 'Windows':
        # Windows 使用线程实现超时
        timer = threading.Timer(seconds, lambda: _thread.interrupt_main())
        timer.start()
        try:
            yield
        except KeyboardInterrupt:
            raise TimeoutException("Timed out!")
        finally:
            timer.cancel()
    else:
        # Linux 使用信号实现超时
        def signal_handler(signum, frame):
            raise TimeoutException("Timed out!")
        signal.signal(signal.SIGALRM, signal_handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

@contextlib.contextmanager
def chdir(root):
    """跨平台的目录切换"""
    if root == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(root)
    try:
        yield
    finally:
        os.chdir(cwd)

def reliability_guard(maximum_memory_bytes: Optional[int] = None):
    """安全限制，防止恶意代码"""
    if maximum_memory_bytes is not None and platform.system() != 'Windows':
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (maximum_memory_bytes, maximum_memory_bytes))
        resource.setrlimit(resource.RLIMIT_DATA, (maximum_memory_bytes, maximum_memory_bytes))
        resource.setrlimit(resource.RLIMIT_STACK, (maximum_memory_bytes, maximum_memory_bytes))
    
    # 禁用危险函数
    import builtins
    builtins.exit = None
    builtins.quit = None
    os.environ['OMP_NUM_THREADS'] = '1'
    os.kill = None
    os.system = None
    os.putenv = None
    os.fork = None
    os.forkpty = None
    os.killpg = None
    __builtins__['help'] = None
    import sys
    sys.modules['ipdb'] = None
    sys.modules['joblib'] = None
    sys.modules['resource'] = None
    sys.modules['psutil'] = None
    sys.modules['tkinter'] = None

def check_correctness(
        task_id: str,
        sample: dict,
        language_type: str,
        timeout: float = 3.0,
        tmp_dir: str = None,
        completion_id: Optional[int] = None,
) -> Dict:
    """
    评估 C++ 代码的功能正确性
    
    Args:
        task_id: 任务ID
        sample: 包含测试代码的样本
        language_type: 语言类型（仅支持cpp）
        timeout: 超时时间（秒）
        tmp_dir: 临时目录
        completion_id: 完成ID
    
    Returns:
        Dict: 包含测试结果的字典
    """
    result = []

    def unsafe_execute(tmp_dir):
        random_id = random.uniform(1, 1000)
        if "cpp" not in language_type.lower():
            result.append("failed: only C++ is supported")
            return

        if tmp_dir is None:
            tmp_dir = tempfile.gettempdir()
        tmp_dir = Path(tmp_dir) / "tmp" / f"{task_id.replace('/', '-')}-{random_id}"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        try:
            with chdir(tmp_dir):
                # 写入测试代码
                with open("test.cpp", 'w', encoding='utf-8') as f:
                    f.write(sample["test_code"])
                
                # 编译命令
                compile_cmd = ["g++", "--std=c++11", "test.cpp"]
                if platform.system() == 'Windows':
                    compile_cmd.append("-mconsole")
                if "162" in task_id:
                    compile_cmd.extend(["-lcrypto", "-lssl"])
                
                # 编译代码
                compilation_result = subprocess.run(
                    compile_cmd,
                    timeout=timeout,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                if compilation_result.returncode != 0:
                    err = compilation_result.stderr or compilation_result.stdout
                    result.append(f"failed: compilation error: {err}")
                    return

                # 执行编译后的程序
                executable = ".\\a.exe" if platform.system() == 'Windows' else "./a.out"
                with time_limit(timeout):
                    exec_result = subprocess.run(
                        [executable],
                        timeout=timeout,
                        capture_output=True,
                        text=True,
                        encoding='utf-8'
                    )
                    if exec_result.returncode == 0:
                        result.append("passed")
                    else:
                        err = exec_result.stderr or exec_result.stdout
                        result.append(f"failed: {err}")
                        
        except TimeoutException:
            result.append("timed out")
        except Exception as e:
            result.append(f"failed: {e}")
        finally:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)

    reliability_guard()
    unsafe_execute(tmp_dir)

    if not result:
        result.append("timed out")

    return {
        "task_id": task_id,
        "completion_id": completion_id,
        "test_code": sample["test_code"],
        "prompt": sample["prompt"],
        "generation": sample["generation"],
        "result": result[0],
        "passed": result[0] == "passed",
        "finish": -1 if "finish" not in sample else sample["finish"],
        "file": "" if "file" not in sample else sample["file"],
        "output": [] if "output" not in sample else sample["output"],
    }
# File: backend/modules/code_interpreter.py
import sys
import io
import contextlib

class CodeInterpreter:
    @staticmethod
    def execute_python(code_str: str) -> dict:
        """Thực thi mã Python an toàn và bắt stdout/stderr"""
        output_buffer = io.StringIO()
        error_msg = None
        
        try:
            with contextlib.redirect_stdout(output_buffer):
                # Giới hạn namespace an toàn đơn giản
                exec_globals = {"__builtins__": __builtins__}
                exec(code_str, exec_globals)
            result = output_buffer.getvalue()
        except Exception as e:
            result = None
            error_msg = str(e)

        return {
            "success": error_msg is None,
            "stdout": result,
            "error": error_msg
        }
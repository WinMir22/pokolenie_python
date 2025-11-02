import codecs
import os
import re
import sys
import traceback
from contextlib import (
    contextmanager,
    nullcontext,
    redirect_stderr,
    redirect_stdout,
)
from io import StringIO
from typing import ContextManager

sys.stdout = codecs.getwriter("utf8")(sys.stdout.buffer)


@contextmanager
def no_stdout():
    with open(os.devnull, "w") as devnull:
        with redirect_stdout(devnull), redirect_stderr(devnull):
            yield


def read_file(path: str | None = None, file_obj=None) -> list[str]:
    if file_obj is not None:
        text = file_obj.read()
    elif path is not None:
        with open(path, encoding="utf-8") as file:
            text = file.read()
    else:
        raise ValueError("Either path or file_obj must be provided")

    return re.split(r"# TEST_.+?:", text)


def clean_output(output: str) -> str:
    lines = [line.strip() for line in output.split("\n")]
    lines = [line for line in lines if line.strip()]
    return "\n".join(lines)


def check_test(
    code: str, expected_output: str, test_number: int, user_code: str
) -> bool:
    print("==================================")
    try:
        code_result = user_code + "\n" + code
        output_buffer = StringIO()
        with redirect_stdout(output_buffer):
            exec(code_result, globals=globals().copy())

        actual_output = output_buffer.getvalue()

        cleaned_actual = clean_output(actual_output)
        cleaned_expected = clean_output(expected_output)

        if cleaned_actual == cleaned_expected:
            print(f"✅ TEST {test_number} ПРОЙДЕН!!!")
            return True
        else:
            print(f"❌ TEST {test_number} ПРОВАЛЕН!!!")
            print("Ожидаемый вывод:")
            print(cleaned_expected)
            print("Фактический вывод:")
            print(cleaned_actual)
            return False

    except Exception:
        print(f"❌ TEST {test_number} ПРОВАЛЕН С ИСКЛЮЧЕНИЕМ!!!")
        traceback.print_exc()
        return False
    finally:
        print("==================================\n\n")


def check_code(
    my_code_file: str,
    input_file: str = "input.txt",
    output_file: str = "output.txt",
    test_results_file: str | None = None,
) -> None:
    if not isinstance(my_code_file, str):
        raise ValueError(f"File path must be str, not {type(my_code_file)}")

    if not isinstance(input_file, str):
        raise ValueError(f"File path must be str, not {type(input_file)}")

    if not isinstance(output_file, str):
        raise ValueError(f"File path must be str, not {type(output_file)}")

    if test_results_file is not None and not isinstance(
        test_results_file, str
    ):
        raise ValueError(
            f"File path must be str, not {type(test_results_file)}"
        )

    if not os.path.exists(my_code_file):
        raise FileNotFoundError(f"Code file not found: {my_code_file}")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if not os.path.exists(output_file):
        raise FileNotFoundError(f"Output file not found: {output_file}")

    if not os.path.isfile(my_code_file):
        raise ValueError(f"Path must be a file, not directory: {my_code_file}")

    if not os.path.isfile(input_file):
        raise ValueError(f"Path must be a file, not directory: {input_file}")

    if not os.path.isfile(output_file):
        raise ValueError(f"Path must be a file, not directory: {output_file}")

    if test_results_file is not None:
        test_results_dir = os.path.dirname(test_results_file)
        if test_results_dir and not os.path.exists(test_results_dir):
            raise FileNotFoundError(
                f"Directory for results file doesn't exist: {test_results_dir}"
            )

        if os.path.exists(test_results_file) and not os.path.isfile(
            test_results_file
        ):
            raise ValueError(
                "Results path must be a file, not directory:"
                f"{test_results_file}"
            )

    try:
        if test_results_file is None:
            stdout_context: ContextManager = nullcontext()
            stderr_context: ContextManager = nullcontext()
            results_file = None
        else:
            results_file = open(test_results_file, "w", encoding="utf8")
            stdout_context = redirect_stdout(results_file)
            stderr_context = redirect_stderr(results_file)

        with (
            stdout_context,
            stderr_context,
            open(my_code_file, encoding="utf8") as code_file,
            open(input_file, encoding="utf8") as input_f,
            open(output_file, encoding="utf8") as output_f,
        ):
            input_tests = read_file(file_obj=input_f)
            output_tests = read_file(file_obj=output_f)
            user_code = code_file.read()

            input_tests = input_tests[1:]
            output_tests = output_tests[1:]

            for i, (test, expected) in enumerate(
                zip(input_tests, output_tests), 1
            ):
                check_test(test, expected, i, user_code)

    finally:
        if results_file:
            results_file.close()

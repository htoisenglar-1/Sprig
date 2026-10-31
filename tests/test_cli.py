"""Exercise the public command line in fresh Python processes."""

import os
import io
from pathlib import Path
import signal
import select
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def cli(self, *arguments, stdin=''):
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        return subprocess.run(
            [sys.executable, '-m', 'sprig', *map(str, arguments)],
            input=stdin, text=True, capture_output=True, cwd=PROJECT,
            env=env, timeout=10,
        )

    def file_cli(self, source, *arguments, suffix='.sprig'):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / ('program' + suffix)
            path.write_text(source, encoding='utf-8')
            return self.cli(*arguments, path)

    def test_help_and_version(self):
        help_result = self.cli('--help')
        self.assertEqual(help_result.returncode, 0)
        self.assertIn('--max-steps', help_result.stdout)
        version = self.cli('--version')
        self.assertEqual(version.returncode, 0)
        self.assertIn('0.1.0', version.stdout)

    def test_file_execution(self):
        result = self.file_cli('print("Hello", 2 + 3)\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'Hello 5\n')
        self.assertEqual(result.stderr, '')

    def test_script_arguments_include_options_after_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'args.sprig'
            path.write_text('print(args)\n', encoding='utf-8')
            result = self.cli(path, 'Ada', '--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '["Ada", "--help"]\n')

    def test_runtime_error_has_location_and_no_traceback(self):
        result = self.file_cli('let x = 1\nprint(x / 0)\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('program.sprig:2:', result.stderr)
        self.assertIn('RuntimeError', result.stderr)
        self.assertIn('^', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_syntax_error_has_no_traceback(self):
        result = self.file_cli('let = 3\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('SyntaxError', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_unterminated_block_fails(self):
        result = self.file_cli('when true:\n print("hello")\n')
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('Traceback', result.stderr)

    def test_lexical_error_has_no_traceback(self):
        result = self.file_cli('print("unterminated)\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('LexError', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_missing_file_and_wrong_extension(self):
        missing = self.cli(PROJECT / 'file-that-does-not-exist.sprig')
        self.assertEqual(missing.returncode, 1)
        self.assertNotIn('Traceback', missing.stderr)
        extension = self.file_cli('print(1)', suffix='.txt')
        self.assertIn(extension.returncode, (1, 2))
        self.assertNotIn('Traceback', extension.stderr)

    def test_invalid_utf8_has_no_traceback(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'invalid.sprig'
            path.write_bytes(b'\xff\xfe')
            result = self.cli(path)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('Traceback', result.stderr)

    def test_tokens_inspection_does_not_execute(self):
        result = self.file_cli('print(missing)\n', '--tokens')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('IDENTIFIER', result.stdout)
        self.assertIn('EOF', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_ast_inspection_does_not_execute(self):
        result = self.file_cli('print(missing)\n', '--ast')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Call', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_debug_flags_are_mutually_exclusive(self):
        result = self.file_cli('print(1)', '--tokens', '--ast')
        self.assertEqual(result.returncode, 2)

    def test_max_steps_stops_program(self):
        result = self.file_cli('while true:\nend\n', '--max-steps', '50')
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('Traceback', result.stderr)

    def test_max_steps_must_be_positive(self):
        for value in ['0', '-1', 'abc']:
            with self.subTest(value=value):
                self.assertEqual(self.cli('--max-steps', value).returncode, 2)

    def test_repl_keeps_variables_and_recovers_after_error(self):
        result = self.cli(stdin='let score = 2\nprint(missing)\nscore = score + 3\nprint(score)\n:quit\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('5\n', result.stdout)
        self.assertIn('RuntimeError', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_repl_accepts_multiline_function(self):
        result = self.cli(stdin='fn double(x):\n return x * 2\nend\nprint(double(6))\n:quit\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('12\n', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_repl_reset_and_help(self):
        result = self.cli(stdin='let n = 1\n:help\n:reset\nlet n = 2\nprint(n)\n:quit\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(':quit', result.stdout)
        self.assertIn('2\n', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_repl_eof_in_block_reports_error(self):
        result = self.cli(stdin='when true:\n print(1)\n')
        self.assertIn('SyntaxError', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_repl_ctrl_c_cancels_only_current_buffer(self):
        from sprig.repl import repl

        class InterruptedInput:
            def __init__(self):
                self.lines = iter(['let n = 7\n', 'fn unfinished():\n', KeyboardInterrupt(), 'print(n)\n', ':quit\n'])

            def readline(self):
                line = next(self.lines, '')
                if isinstance(line, BaseException):
                    raise line
                return line

        stdout, stderr = io.StringIO(), io.StringIO()
        status = repl(stdin=InterruptedInput(), stdout=stdout, stderr=stderr)
        self.assertEqual(status, 0)
        self.assertIn('Input cancelled.', stdout.getvalue())
        self.assertIn('7\n', stdout.getvalue())
        self.assertEqual(stderr.getvalue(), '')

    def test_old_repl_function_error_points_to_its_body(self):
        result = self.cli(stdin='fn bad():\n return 1 / 0\nend\nbad()\n:quit\n')
        self.assertIn('return 1 / 0', result.stderr)
        self.assertIn('RuntimeError', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    @unittest.skipIf(os.name == 'nt', 'POSIX signal test')
    def test_ctrl_c_file_execution_returns_130(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'loop.sprig'
            path.write_text('print("ready")\nwhile true:\nend\n', encoding='utf-8')
            child = subprocess.Popen(
                [sys.executable, '-u', '-m', 'sprig', str(path)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=PROJECT,
            )
            try:
                ready, _, _ = select.select([child.stdout], [], [], 5)
                self.assertTrue(ready, 'Program did not reach its ready message')
                self.assertEqual(child.stdout.readline(), 'ready\n')
                child.send_signal(signal.SIGINT)
                stdout, stderr = child.communicate(timeout=5)
                self.assertEqual(child.returncode, 130)
                self.assertNotIn('Traceback', stderr)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.communicate()


if __name__ == '__main__':
    unittest.main()

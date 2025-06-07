import gdb
import subprocess
import threading
import os
import signal
import time

# Define the "rt" command
def interrupt_after_delay(delay=5):
    def interrupt():
        print(f"[*] Forcing Ctrl+C after {delay} seconds...")
        os.kill(os.getpid(), signal.SIGINT)  # Simulate Ctrl+C
    timer = threading.Timer(delay, interrupt)
    timer.start()
class RemoteTarget(gdb.Command):
    """Attach Remote a process from gdbserver.
    Usage:
      rt <process_name>  - First invocation with a process name.
      rt                 - Reuse the last process name.
    """

    def __init__(self):
        super(RemoteTarget, self).__init__("rt", gdb.COMMAND_USER)
        self.saved_library = None
        self.status = None
        self.debug_folder = '/tmp/gdb-debug/'
        self.host_target = ":1234"

        # Hook events
        gdb.events.exited.connect(self._process_close)

    def _process_close(self, event):
        self.status = False

    def invoke(self, argument, from_tty):
        args = gdb.string_to_argv(argument)
        if self.status:
            gdb.write(f"Error: Remote Target already running!\n", gdb.STDERR)
            return
        elif len(args) == 2:
            self.host_target = f"{args[0]}:{args[1]}"

        try:
            gdb.execute(f"target remote {self.host_target}")
            if not self.saved_library: interrupt_after_delay(60)
            gdb.write(f"Connected to remote target on {self.host_target}.\n")
            gdb.execute("c")
        except Exception as e:
            gdb.write(f"Error: {e}\n", gdb.STDERR)
        
        if not self.saved_library:
            __import__('shutil').rmtree(self.debug_folder, ignore_errors=True)
            libs = gdb.execute("info sharedlibrary", to_string=True)
            for line in libs.splitlines():
                if "target:" in line:
                    path = line.split()[-1][7:]  # Get full path like /lib/x86_64-linux-gnu/libc.so.6 and trim target:
                    filename = os.path.basename(path)
                    local_dir = self.debug_folder + os.path.dirname(path)
                    local_path = os.path.join(local_dir, filename)
                    os.makedirs(local_dir, exist_ok=True)
                    try:
                        print(f"Downloading {path} -> {local_path}")
                        gdb.execute(f'remote get {path} {local_path}')
                    except gdb.error as e:
                        print(f"Failed to download {path}: {e}")
            self.saved_library=True
            gdb.execute(f"set sysroot {self.debug_folder}")
            gdb.execute("c")
        self.status = True

# Define the "at" command
class AttachToProcess(gdb.Command):
    """Attach to a process by name using pgrep.
    Usage:
      at <process_name>  - First invocation with a process name.
      at                 - Reuse the last process name.
    """
    
    def __init__(self):
        super(AttachToProcess, self).__init__("at", gdb.COMMAND_USER)
        self.current_process_name = None
        self.status = None

        # Hook events
        gdb.events.exited.connect(self._process_close)

    def _process_close(self, event):
        self.status = False

    def invoke(self, argument, from_tty):
        args = gdb.string_to_argv(argument)
        if self.status:
            gdb.write(f"Error: Attach Process already running!\n", gdb.STDERR)
            return
        elif not self.current_process_name:
            if len(args) != 1:
                gdb.write("Usage: at <process_name>\n", gdb.STDERR)
                return
            self.current_process_name = args[0]

        try:
            # Use pgrep to find the PID of the process
            output = subprocess.run([f'pgrep -lf {self.current_process_name}'], capture_output=True, text=True, shell=True).stdout
            for line in output.strip().split('\n'):
                if line.split()[1] in ['gdb', 'sudo']: continue
                pid = int(line.split()[0])
            # Attach to the process
            gdb.execute(f'attach {pid}')
            gdb.write(f"Attached to process '{self.current_process_name}' with PID {pid}.\n")
            self.status = True
            gdb.execute("c")
        except subprocess.CalledProcessError:
            gdb.write(f"No process found with the name '{self.current_process_name}'.\n", gdb.STDERR)
            self.current_process_name = None
        except ValueError:
            gdb.write("Failed to parse the PID.\n", gdb.STDERR)
            self.current_process_name = None
        except Exception as e:
            gdb.write(f"attach error: {str(e)}\n", gdb.STDERR)
            self.current_process_name = None


gdb.execute("set pagination off")
# Register the "rt" command
RemoteTarget()
# Register the "at" command
AttachToProcess()
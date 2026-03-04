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
        os.kill(os.getpid(), signal.SIGINT)  # simulate Ctrl+C
    timer = threading.Timer(delay, interrupt)
    timer.start()

class RemoteTarget(gdb.Command):
    def print_help(self):
        msg='''
Attach Remote a process from gdbserver/qemu.
    Usage:
      rt                 - auto remote connect to :1234
      rt host:port       - auto remote connect to host:port
      rt c               - disable/enable continue after using command
'''
        gdb.write(msg, gdb.STDERR);

    # best-effort check: are we on a remote target and is the link alive?
    def remote_is_connected(self):
        try:
            if "Remote" not in gdb.execute("show target", to_string=True):
                return False
            # prefer packet ping; fall back to threads()
            try:
                gdb.execute("maintenance packet qSupported", to_string=True)
                return True
            except gdb.error:
                gdb.selected_inferior().threads()
                return True
        except gdb.error:
            return False

    def __init__(self):
        super(RemoteTarget, self).__init__("rt", gdb.COMMAND_USER)
        self.saved_library = None
        self.status = None
        self.debug_folder = '/tmp/gdb-debug/'
        self.host_target = ":1234"
        self.continue_on_attach = False

        # Hook events
        gdb.events.exited.connect(self._process_close)

    def _process_close(self, event):
        self.status = False

    def invoke(self, argument, from_tty):
        args = gdb.string_to_argv(argument)
        # if self.status:
        if self.remote_is_connected():
            gdb.write(f"Error: Remote Target already running!\n", gdb.STDERR)
            return
        elif len(args) == 1:
            if ':' in args[0]:
                self.host_target = args[0]
            elif args[0] == 'c':
                self.continue_on_attach ^= True
                gdb.write("[rt] continue is %s.\n" % ("enable" if self.continue_on_attach else "disable"))
            else:
                self.print_help(); return

        try:
            if self.host_target == ":1234":
                output = subprocess.run(['netstat -ntlp|grep 1234'], capture_output=True, text=True, shell=True).stdout
                if self.host_target not in output:
                    gdb.write(f"Error: No Local Remote Target present!\n", gdb.STDERR)
                    return
            gdb.execute(f"target remote {self.host_target}")
            # check if target is qemu -s
            # features = gdb.execute("maintenance print frame-id", to_string=True).lower()
            # if "stack=0xffffffff" not in features:
                # self.saved_library=True
            # delay and interrupt to saved remote library
            # elif not self.saved_library: interrupt_after_delay(30)
            self.saved_library = True
            gdb.write(f"Connected to remote target on {self.host_target}.\n")
            if self.continue_on_attach:
                gdb.execute("c")
        except Exception as e:
            gdb.write(f"Error: {e}\n", gdb.STDERR)
        
        ## if remote target from gdbserver, still on dev ##
        if not self.saved_library:
            __import__('shutil').rmtree(self.debug_folder, ignore_errors=True)
            libs = gdb.execute("info sharedlibrary", to_string=True)
            for line in libs.splitlines():
                if "target:" in line:
                    # get full path like /lib/x86_64-linux-gnu/libc.so.6 and trim target:
                    path = line.split()[-1][7:]
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
    def print_help(self):
        msg='''
Attach to a process by name using pgrep.
    Usage:
      at <process_name>  - first invocation with a process name (optional)
      at                 - reuse the last process name.
'''
        gdb.write(msg, gdb.STDERR);
    
    def __init__(self):
        super(AttachToProcess, self).__init__("at", gdb.COMMAND_USER)
        self.current_process_name = None
        self.status = None
        self.pid = None

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
                gdb.write(f"Usage: at {os.path.basename(gdb.current_progspace().filename)}\n", gdb.STDERR)
                self.current_process_name = os.path.basename(gdb.current_progspace().filename)
            else:
                if args[0] in ['-h', 'help', '--help']:
                    self.print_help(); return                    
                self.current_process_name = args[0]

        try:
            # Use pgrep to find the PID of the process
            output = subprocess.run([f'pgrep -alf {self.current_process_name}'], capture_output=True, text=True, shell=True).stdout
            for line in output.strip().split('\n'):
                pid, cmd, *rest = line.split()
                # print(f'''"{self.current_process_name}" == "{line.split()[1]}"''')
                # if line.split()[1] in ['gdb', 'sudo']: continue
                # elif self.current_process_name in output:
                #     self.pid = int(line.split()[0])
                #     break
                if os.path.basename(cmd) == self.current_process_name:
                    self.pid = int(pid)
                    break
            # Attach to the process
            gdb.execute(f'attach {self.pid}')
            gdb.write(f"Attached to process '{self.current_process_name}' with PID {self.pid}.\n")
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

def register():
    RemoteTarget()
    AttachToProcess()
> hmm idk, this is just my personal project

> how2run ?
$ docker build -t my-gdb .
$ docker run -it --rm \
  --pid=host \
  --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  -v /proc:/host_proc \
  -v /:/mnt/host \
  my-gdb \
  bash
> hmm idk, this is just my personal ̶p̶r̶o̶j̶e̶c̶t̶  note

> how2run ?
$ docker build -t my-gdb .
$ docker run -it --rm \
  --pid=host \
  --network=host \
  --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  --privileged \
  my-gdb \
  gefk
OR
$ docker-compose up --build

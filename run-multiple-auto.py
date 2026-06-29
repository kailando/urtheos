from subprocess import Popen, run
import sys
try:

    args = sys.argv[2:]
    n = int(sys.argv[1])

    procs = []
    files = []
    for i in range(n):
        files.append(open(f"instance{i+1}.txt", "wt", encoding="utf-8"))
        procs.append(Popen([
            'python',
            'auto.py',
            *args
        ], cwd='src', stdout=files[i], stderr=files[i]))

    while True:
        not_running = 0
        for proc in procs:
            if proc.poll() is None:
                continue
            not_running += 1
        if not_running == n:
            break

    for f in files:
        f.close()

    for proc in procs:
        if proc.returncode:
            sys.exit(1)
    sys.exit(0)
finally:
    run("./remove-instancelogs")

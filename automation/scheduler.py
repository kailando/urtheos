"""Skeleton for automation script

This is a minimal template that imports the automation API
and provides a skeleton for implementing your own scheduler.

To use:
1. Copy this file anywhere in the project to create your own automation script
2. Implement the schedule() method in the MyScheduler class
3. Run with: pipenv run auto your_script.py

Globals available:
- `num_cpus`: number of available CPUs
- `cpu_core_types`: list of core types for each CPU, either 'STANDARD', 'PERFORMANCE', or 'EFFICIENT'
- `num_ram_pages`: number of pages that fit on RAM  
- `num_swap_pages`: number of pages that fit on SWAP

See automation/api.py for full documentation of the API.
"""
from automation import Scheduler
from copy import deepcopy
from contextlib import suppress

INF = float('inf')

class RealScheduler(Scheduler):
    """A working, if not on-the-edge scheduler
    
    Override the schedule() method to implement your scheduling logic.
    
    Available state:
        procs_headcanon: dict[int, Process] - all active processes
        self.pages: dict[tuple[int,int], Page] - all memory pages
        self.used_cpus: int - number of CPUs currently in use
        self.io_queue.io_count: int - number of I/O events ready
    
    Available actions:
        self.move_process(pid) - toggle process on/off CPU
        self.move_page(pid, idx) - swap page between RAM and disk
        self.do_io() - process one I/O event
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.healthy=[]
        self.starving=[]
        self.dead=[]
    
    def preprocess(self):
        it = list(self.processes.items())

        self.starving = []
        for pid, proc in it:
            if proc.has_cpu:
                continue
            if proc.starvation_level == 0:
                continue
            if proc.time_to_termination == INF:
                continue
            self.starving.append(pid)
        def key(pid) -> float:
            proc=self.processes[pid]
            return proc.time_to_termination
        self.starving.sort(
            key = key,
            reverse = False
        )
        self.starving = self.starving[:num_cpus]
        
        self.healthy = []
        for pid, proc in it:
            if not proc.has_cpu:
                continue
            if proc.starvation_level:
                continue
            if proc.time_to_termination != INF:
                continue
            self.healthy.append(pid)

        self.dead = []
        for pid, proc in it:
            if not proc.has_ended:
                continue
            self.dead.append(pid)

    # def __call__(self, *args, **kwargs):
        # self.preprocess()
        # return super().__call__(*args, **kwargs)
    
    def schedule(self):
        """Implement your scheduling algorithm here.
        
        This method is called once per frame after all game events
        have been processed. Read the current state and use the
        action methods to control the game.
        """
        self.preprocess()
        with suppress(BaseException):
            global num_cpus, num_ram_pages
            procs_headcanon = deepcopy(self.processes)

            # Quickly handle I/O
            for _ in range(self.io_queue.io_count):
                self.do_io()
        
            # Populate CPUs if not populated
            if len(procs_headcanon) == 0:
                return
            if self.used_cpus < num_cpus:
                count=self.used_cpus
                for pid, proc in procs_headcanon.items():
                    if count == num_cpus:
                        break
                    if proc.has_cpu:
                        continue
                    self.move_process(pid)
                    count += 1
            
            # Kill dead
            for pid in self.dead:
                self.move_process(pid)
                del procs_headcanon[pid]
            
            # Move out all of the healthy procs
            for pid in self.healthy:
                self.move_process(pid)
                procs_headcanon[pid].has_cpu = False
            
            # Move in the starving procs
            for pid in self.starving:
                self.move_process(pid)
                procs_headcanon[pid].has_cpu = True

            # Handle pages
            for pid, proc in procs_headcanon.items():
                for page in proc.pages:
                    if page.waiting_to_swap or page.swap_in_progress:
                        continue
                    if proc.has_cpu and page.on_disk:
                        self.move_page(pid, page.idx)
                    elif (not proc.has_cpu) and (not page.on_disk):
                        self.move_page(pid, page.idx)
            


# The game expects a callable named `scheduler`
scheduler = RealScheduler()

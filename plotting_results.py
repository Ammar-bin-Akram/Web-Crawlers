import re
import matplotlib.pyplot as plt

# Read the input file
with open("crawl_results.txt", "r") as file:
    data = file.read()

# Extract timings using regex
serial_time = float(re.search(r"Total time taken:\s*([\d.]+)\s*seconds", data).group(1))

# Multithreading times
mt_matches = re.findall(r"Number of threads:\s*(\d+)\s*Total time elapsed:\s*([\d.]+)", data)
mt_times = {int(threads): float(time) for threads, time in mt_matches}

# MPI times
mpi_matches = re.findall(r"Number of workers:\s*(\d+)\s*Total time taken:\s*([\d.]+)", data)
mpi_times = {int(workers): float(time) for workers, time in mpi_matches}

# Plotting
labels = ['Serial', 'MT-2', 'MT-4', 'MPI-2', 'MPI-4']
times = [serial_time, mt_times[2], mt_times[4], mpi_times[2], mpi_times[4]]

plt.figure(figsize=(10, 6))
plt.bar(labels, times, color=['gray', 'blue', 'blue', 'green', 'green'])
plt.title("Crawling Time Comparison: Serial vs Multithreading vs MPI")
plt.ylabel("Time (seconds)")
plt.xlabel("Execution Mode")
plt.grid(axis='y')
plt.tight_layout()
plt.show()

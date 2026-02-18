import matplotlib.pyplot as plt
import numpy as np

def plot_percentage(x):
    percentages = []
    for i in range(1, x+1):
        numbers_starting_with_1 = len([str(j) for j in range(1, i+1) if str(j)[0] == '1'])
        percentage = (numbers_starting_with_1 / i) * 100
        percentages.append(percentage)
    plt.plot(range(1, x+1), percentages, color='black')
    plt.xlabel('x')
    plt.ylabel('Percentage of numbers starting with 1')
    plt.title('Percentage of numbers starting with 1 vs x')
    plt.xscale('log')
    plt.show()

plot_percentage(2000)

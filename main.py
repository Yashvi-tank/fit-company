#!/usr/bin/env python
from src.fit.app import run_app
from src.fit.services.fitness_data_init import init_fitness_data

init_fitness_data()


if __name__ == "__main__":
    run_app() 
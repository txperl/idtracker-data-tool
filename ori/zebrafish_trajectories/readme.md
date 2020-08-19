# idtracker.ai zebrafish trajectories

## Info

This folder contains trajectories of juvenile zebrafish obtained and used in [1, 2].
Details about the experimental setup, videos and animals can be found in [1, 2].
If you use these trajectories in your research please cite [1, 2].

## Directory structure

    .
    ├── readme.md     # This file
    ├── 10            # 3 sets of trajectories of 10 juvenile zebrafish [1]
        ├── 1            
            ├── trajectories.npy            # trajectories with gaps during the crossings of the animals.
            └── trajectories_wo_gaps.npy    # trajectories without gaps during the crossings of the animals.
        ├── 2
            └── ...
        └── 3
            └── ...            
    ├── 60           # 3 sets of trajectories of 60 juvenile zebrafish [1, 2]
        └── ...          
    ├── 80           # 3 sets of trajectories of 80 juvenile zebrafish [2]  
        └── ...            
    └── 100          # 3 sets of trajectories of 100 juvenile zebrafish [1, 2]  
        └── ...            

## How to open .npy files

We recommend to work with the [trajectorytools](https://github.com/fjhheras/trajectorytools) package.
Examples of how to load the data can be found in the [idtracker.ai Jupyter notebooks](https://gitlab.com/polavieja_lab/idtrackerai_notebooks)

To access the raw data, the `.npy` files can be opened in Python using the `np.load()` command from the Numpy library in Python.


## References

[1] [Romero-Ferrero, F., Bergomi, M. G., Hinz, R. C., Heras, F. J., & de Polavieja, G. G. (2019). Idtracker. ai: tracking all individuals in small or large collectives of unmarked animals. Nature methods, 16(2), 179-182.](https://www.nature.com/articles/s41592-018-0295-5)
[2] [Heras, F. J., Romero-Ferrero, F., Hinz, R. C., & de Polavieja, G. G. (2019). Deep attention networks reveal the rules of collective motion in zebrafish. PLoS computational biology, 15(9), e1007354.](https://journals.plos.org/ploscompbiol/article/authors?id=10.1371/journal.pcbi.1007354)

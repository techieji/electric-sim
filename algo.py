# ======== Variables and functions for the algorithm ========
VERTICES_NOT = []
VERTICES_TOGGLE = []

SHAPE_NOT = (1,1,1,1,1,0,1,1,1)
SHAPE_TOGGLE = (1,1,1,1,1,1,1,1,1)

# Checks if a given position is the center of a shape
# @param ix, iy is upper-left corner of box to be checked
# @return boolean 1 if found 
def compare(ix, iy, shape):
    global arr
    for i in range(0,shape.count()):
        # TODO: implement checking for shapes of other dimensions
        if arr[ix + i%3][iy + i//3] != shape[i]:
            return 0
    return 1

# Iterates over board or region running compare to record vertices of shapes
def find_shapes():
    return 0

# Colors the circuit by iterating through the graph until reaching a marked vertex
def color():
    return 0



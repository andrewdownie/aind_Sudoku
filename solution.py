assignments = []

rows = 'ABCDEFGHI'
cols = '123456789'

def cross(a, b):
    """
    cross each character of two strings 
    Args:
        a(string): first list of characters to be crossed
        b(string): second list of characters to be crossed
    Returns:
        a list with len(a) * len(b) indices, 
        where each index contains two characters,
        one character from string a, and one from string b
    """
    return [s+t for s in a for t in b]

def build_diagonal_units():
    """
    creates the diagonal grouping of cells for diagonal sudoku
    Returns:
        a list containing two sublists:
            - the first sublist holds characters: A1, B2, ... I9 
            - the second sublist holds characters: A9, B8, ... I1
    """
    i = 0
    diagonal = []

    # Create the first sublist: A1, B2, ... I9
    d1 = []
    for i in range(0, len(rows)):
        d1.append(rows[i] + cols[i])

    # Create the second sublist: A9, B8, ... I1
    d2 = []
    for i in range(0, len(rows)):
        d2.append(rows[i] + cols[len(cols) - i - 1])

    # Add the two sublists to a list
    diagonal.append(d1)
    diagonal.append(d2)

    return diagonal

"""
Create all the unit groups we will need for contraint propagation to work.
"""
boxes = cross(rows, cols)
row_units = [cross(r, cols) for r in rows]
column_units = [cross(rows, c) for c in cols]
square_units = [cross(rs, cs) for rs in ('ABC','DEF','GHI') for cs in ('123','456','789')]
diagonal_units = build_diagonal_units() 
unitlist = row_units + column_units + square_units + diagonal_units 
units = dict((s, [u for u in unitlist if s in u]) for s in boxes)
peers = dict((s, set(sum(units[s],[]))-set([s])) for s in boxes)

def assign_value(values, box, value):
    """
    Assigns a value to a given box.
    """
    # Don't waste memory appending actions that don't actually change any values
    if values[box] == value:
        return values

    # Assign the value
    values[box] = value
    # If the box has one value, then we've solved it, and we should add it to the assignments list so it can be displayed by pygame
    if len(value) == 1:
        assignments.append(values.copy())
    return values

def naked_twins(values):
    """
    Eliminate values using the naked twins strategy.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}

    Returns:
        the values dictionary with the naked twins eliminated from peers.
    """
    values_before = values.copy()

    # Go through each cell of the sudoku
    for currentCell in values:
        # If the current cell has two possible values
        if(len(values[currentCell]) == 2):
            # Go through each of the current cells related units
            for unit in units[currentCell]:
                # For each cell in the current unit 
                for unitCell in unit:
                    # Make sure the current cell and current unit cell are not refering to the same cell 
                    #   (Since the currentCell is within the unit we are currently going thorugh)
                    if(currentCell != unitCell):
                        # If the current cell and the current unit cell have the same values
                        if(values[unitCell] == values[currentCell]):
                            # Then we've found a case of naked twins
                            values = apply_naked_twins(values, unit, currentCell, unitCell)

    return values

def apply_naked_twins(values, unit, matchingCell, matchingPeer):
    """
    If a naked twins case is found, this should be called to remove all values from the cells units
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}
        unit(list): the list of cells in the unit related to the found naked twin pair
        value(string): the key to the current box that is part of the found naked twin
        matchingPeer(string): the key to the box that is part of the found naked twin
    """
    # Go through each cell in the unit we found the naked twins in
    for unitCell in unit:
        # If the current  unitCell is not either of the two cells that make up the naked twins
        if(unitCell != matchingCell and unitCell != matchingPeer):
            # Remove the values found in the naked twins from the current unitCell
            values[unitCell] = values[unitCell].replace(values[matchingCell][0], "")
            values[unitCell] = values[unitCell].replace(values[matchingCell][1], "")
    
    return values
 

def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '123456789' for empties.
    Input: A grid in string form.
    Output: A grid in dictionary form
            Keys: The boxes, e.g., 'A1'
            Values: The value in each box, e.g., '8'. If the box has no value, then the value will be '123456789'.
    """
    chars = []
    digits = '123456789'

    # Go through each character of the 81 character string
    for c in grid:
        # If the character is a number 1..9 then add it to the list as is
        if c in digits:
            chars.append(c)
        # Otherwise, if the character is a period, add the characters 1..9 to show that it could hold any value
        if c == '.':
            chars.append(digits)
    assert len(chars) == 81
    # Match each character from the list we just created, with every sudoku board index in order to create a dictionary
    return dict(zip(boxes, chars))

def display(values):
    """
    Display the values as a 2-D grid.
    Input: The sudoku in dictionary form
    Output: None
    """

    # Calculate the width of box
    width = 1+max(len(values[s]) for s in boxes)

    # Create the line that splits square units horizontally 
    line = '+'.join(['-'*(width*3)]*3)

    # Go through each row, and print each line after formating it
    for r in rows:
        print(''.join(values[r+c].center(width)+('|' if c in '36' else '')
                      for c in cols))
        if r in 'CF': print(line)
    return

def eliminate(values):
    """
    Go through all the boxes, and whenever there is a box with a value, eliminate this value from the values of all its peers.
    Input: A sudoku in dictionary form.
    Output: The resulting sudoku in dictionary form.
    """
    # Get a list of all the boxes on the board that have been solved
    solved_values = [box for box in values.keys() if len(values[box]) == 1]
    # Go though each box that is solved
    for box in solved_values:
        # get the digit from the current box
        digit = values[box]
        # Go through each peer of the current box
        for peer in peers[box]:
            # Remove the digit from the solved box from all other boxes that share that unit
            values[peer] = values[peer].replace(digit,'')
    return values

def only_choice(values):
    """
    Go through all the units, and whenever there is a unit with a value that only fits in one box, assign the value to this box.
    Input: A sudoku in dictionary form.
    Output: The resulting sudoku in dictionary form.
    """
    # Go through every unit in the board
    for unit in unitlist:
        # Go through every valid sudoku digit
        for digit in '123456789':
            # Create a list that contains all the possible locations for the current digit
            dplaces = [box for box in unit if digit in values[box]]
            # If there is only one possible place for the current digit
            if len(dplaces) == 1:
                # Then place that digit in the only spot it can go
                values[dplaces[0]] = digit
    return values

def reduce_puzzle(values):
    """
    Iterate eliminate() and only_choice(). If at some point, there is a box with no available values, return False.
    If the sudoku is solved, return the sudoku.
    If after an iteration of both functions, the sudoku remains the same, return the sudoku.
    Input: A sudoku in dictionary form.
    Output: The resulting sudoku in dictionary form.
    """

    # Find all cells that have been solved
    solved_values = [box for box in values.keys() if len(values[box]) == 1]
    stalled = False

    # Keep looping until a stall is detected
    while not stalled:
        # Count how many values were solved before
        solved_values_before = len([box for box in values.keys() if len(values[box]) == 1])
        # Apply all of our strategies to solve the board
        values = eliminate(values)
        values = only_choice(values)
        values = naked_twins(values)
        # Count how many values are solved after
        solved_values_after = len([box for box in values.keys() if len(values[box]) == 1])
        # If we haven't solved any additional cells, then we are getting no where
        stalled = solved_values_before == solved_values_after

        # TODO: I'm not sure what this does atm......................................................................
        if len([box for box in values.keys() if len(values[box]) == 0]):
            print("reduce puzzle returned false")
            return False
    return values

def search(values):
    """
    Using depth-first search and propagation, create a search tree and solve the sudoku.
    """
    # First, reduce the puzzle using the previous function
    values = reduce_puzzle(values)
    # Choose one of the unfilled squares with the fewest possibilities
    if values is False:
        print("Search returned false ---- ")
        return False# reduce found the puzzle to be unsolvable
    if all(len(values[s]) == 1 for s in boxes):
        return values#there is exactly one value in every box, so we solved it!
    
    # chose one of the unfilled squares with the fewest possibilities
    n,s = min((len(values[s]), s) for s in boxes if len(values[s]) > 1)

    
    # Now use recursion to solve each one of the resulting sudokus, and if one returns a value (not False), return that answer!
    for value in values[s]:
        # copy the current board and assign the value to the cell we want want to search on
        new_sudoku = values.copy()
        new_sudoku[s] = value
        # begin the search
        attempt = search(new_sudoku)
        # if the search was successful, return it up the chain
        if attempt:
            return attempt

def solve(grid):
    """
    Find the solution to a Sudoku grid.
    Args:
        grid(string): a string representing a sudoku grid.
            Example: '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    Returns:
        The dictionary representation of the final sudoku grid. False if no solution exists.
    """
    # convert 81 char board to dictionary board
    values = grid_values(grid)

    # solve the board
    values = search(values)

    return values

if __name__ == '__main__':
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    display(solve(diag_sudoku_grid))


    try:
        from visualize import visualize_assignments
        visualize_assignments(assignments)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')

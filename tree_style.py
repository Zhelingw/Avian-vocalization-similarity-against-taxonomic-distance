"""
CSC111 Project 2: Tree Visualization Style

This module stores the style settings for the tree visualizer.

Usage:
    from tree_style import STYLESHEET

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""
STYLESHEET = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'font-family': 'Courier New',
            'font-size': '14px',
            'border-width': 2,
            'border-color': 'black'
        }
    },
    {
        'selector': '.parent',
        'style': {
            'shape': 'square',
            'width': 40,
            'height': 40,
            'background-color': 'lightgray',
            'text-valign': 'top',
            'text-margin-y': -5
        }
    },
    {
        'selector': '.leaf',
        'style': {
            'shape': 'ellipse',
            'width': 65,
            'height': 65,
            'background-image': 'data(img_url)',
            'background-fit': 'cover',
            'background-color': 'data(tint_color)',
            'background-image-opacity': 'data(img_opacity)',
            'text-valign': 'bottom',
            'text-margin-y': 5
        }
    },
    {
        'selector': 'edge',
        'style': {
            'width': 2,
            'line-color': 'black',
            'opacity': 0.5,
            'curve-style': 'bezier'
        }
    }
]

if __name__ == '__main__':
    import python_ta
    import doctest

    python_ta.check_all(config={
        'extra-imports': [
        ],  # the names (strs) of imported modules
        'allowed-io': [
        ],  # the names (strs) of functions that call print/open/input
        'max-line-length': 120
    })
    doctest.testmod(verbose=True)

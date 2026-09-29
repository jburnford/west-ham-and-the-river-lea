"""Check southern Three Mills source matches and preserved neighbours."""
import argparse
from factory_alignment_checks import check_register


def check(preflight=False):
    check_register('three-mills-south', {f'site419-range-{i}' for i in range(21,29)},
        5, 3, 'three-mills-south-before', preflight,
        later_registers=['three-mills-landmark'], scene_counts=(547,{419:38}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--preflight',action='store_true')
    check(parser.parse_args().preflight)

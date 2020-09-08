import stormpy as sp

import logging

from datastructures.PCFP import PCFP


def test_PCFP_to_jani_from_jani():
    path = "../examples/nand_simple.prism"
    logging.info("loading model {}".format(path))
    prism_program: sp.PrismProgram = sp.parse_prism_program(path)
    prism_props: sp.core.Property = sp.parse_properties_for_prism_program("P=? [F x>=20]", prism_program)
    jani_model, jani_props = prism_program.to_jani(prism_props)

    logging.info("building pcfp from jani ...")
    pcfp = PCFP.from_jani(jani_model)

    logging.info("converting pcfp back to jani ... ")
    jani_model = pcfp.to_jani()

    if not jani_model.has_undefined_constants:
        logging.info("attempting to build the model...")
        sp.build_model(jani_model)

if __name__ == '__main__':
    test_PCFP_to_jani_from_jani()
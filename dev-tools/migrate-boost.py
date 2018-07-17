#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re

test_header_pattern = re.compile("#include \".*\"")
test_suite_pattern = re.compile("CppUnit::Test\*.*::suite\(\) {")
test_case_pattern = re.compile("void \w*::test(\w*)\(\) {")

def skip_block(line, counter):
    return counter + line.count("{") - line.count("}")

def skip_comments(line):
    stripped_line = line.strip()
    # quickly skip comments (does not catch all cases)
    if stripped_line.startswith("//") or stripped_line.startswith("/*") or stripped_line.startswith("*/") :
        return True, line, 0
    return False, line, 0


def remove_suite(line):
    m = test_suite_pattern.match(line)
    if m:
        return True, "", 1
    return False, line, 0

def rewrite_test_suite_header(line):
    m = test_header_pattern.match(line)
    if m:
        # not placed on the right line yet
        return True, "#include <boost/test/unit_test.hpp>", 0
    return False, line, 0


def rewrite_test_case_header(line):
    m = test_case_pattern.match(line)
    if m:
        test_name = m.group(1)
        if not test_name:
            test_name = "simple"
        return True, "BOOST_AUTO_TEST_CASE({}) {{".format(test_name), 0
    return False, line, 0

def rewrite_assert(line):
    rewriten = line.replace("CPPUNIT_ASSERT_EQUAL", "BOOST_CHECK_EQUAL")
    rewriten = rewriten.replace("CPPUNIT_ASSERT", "BOOST_CHECK")

    return line != rewriten, rewriten, 0

if __name__ == '__main__':

    filename = sys.argv[1]

    test_suite_name = os.path.basename(filename)
    content = open(filename).readlines()

    content_out = []

    rewrite_rules = [skip_comments, rewrite_test_suite_header, remove_suite, rewrite_test_case_header, rewrite_assert]
    skip_block_counter = 0
    hit = False
    for line in content:
        if skip_block_counter > 0:
            skip_block_counter = skip_block(line, skip_block_counter)
        else:
            for rule in rewrite_rules:
                hit, rewritten_line, skip_block_counter = rule(line)
                if hit:
                    content_out.append(rewritten_line)
                    print ("rule {} hit".format(rule.__name__))
                    break
            if not hit:
                content_out.append(line)

    with open(filename, "w") as out:
        for l in content_out:
            out.write(l)

#!/usr/bin/env python
# xfail-license

# this combines all the working run-pass tests into a single large crate so we
# can run it "fast": spawning zillions of windows processes is our major build
# bottleneck (and it doesn't hurt to run faster on other platforms as well).

import sys
import os
import codecs


def scrub(b):
    if sys.version_info >= (3,) and type(b) == bytes:
        return b.decode('ascii')
    else:
        return b

src_dir = scrub(os.getenv("CFG_SRC_DIR"))
if not src_dir:
    raise Exception("missing env var CFG_SRC_DIR")

run_pass = os.path.join(src_dir, "src", "test", "run-pass")
run_pass = os.path.abspath(run_pass)
stage2_tests = []

for t in os.listdir(run_pass):
    if t.endswith(".rs") and not (
            t.startswith(".") or t.startswith("#") or t.startswith("~")):
        f = codecs.open(os.path.join(run_pass, t), "r", "utf8")
        s = f.read()
        if not ("xfail-test" in s or
                "xfail-fast" in s or
                "xfail-win32" in s):
            if not "pub fn main" in s and "fn main" in s:
                print("Warning: no public entry point in " + t)
            stage2_tests.append(t)
        f.close()

stage2_tests.sort()

c = open("tmp/run_pass_stage2.rc", "w")
i = 0
c.write(
"""
// AUTO-GENERATED FILE: DO NOT EDIT
#[crate_id=\"run_pass_stage2#0.1\"];
#[crateid=\"run_pass_stage2#0.1\"];
#[feature(globs, macro_rules, struct_variant, managed_boxes)];
#[allow(warnings)];
"""
)
for t in stage2_tests:
    p = os.path.join(run_pass, t)
    p = p.replace("\\", "\\\\")
    c.write("#[path = \"%s\"]" % p)
    c.write("pub mod t_%d;\n" % i)
    i += 1
c.close()


d = open("tmp/run_pass_stage2_driver.rs", "w")
d.write(
"""
// AUTO-GENERATED FILE: DO NOT EDIT
#[feature(globs, managed_boxes)];
extern mod extra;
extern mod run_pass_stage2;
use run_pass_stage2::*;
use std::io;
use std::io::Writer;
fn main() {
    let mut out = io::stdout();
"""
)
i = 0
for t in stage2_tests:
    p = os.path.join("test", "run-pass", t)
    p = p.replace("\\", "\\\\")
    d.write("    out.write(\"run-pass [stage2]: %s\\n\".as_bytes());\n" % p)
    d.write("    t_%d::main();\n" % i)
    i += 1
d.write("}\n")

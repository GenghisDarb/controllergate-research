# v2.8h Boolean Heuristic Inconsistency

v2.8h successfully registered the boolean heuristic and detected that the `youtube-dl:1` unary operator block exists, but patch generation reported `expected UNARY_OPERATORS block not found`. v2.8i fixes this patch-construction mismatch by searching the full `youtube_dl/utils.py` source file and patching the bounded unary-operator region.

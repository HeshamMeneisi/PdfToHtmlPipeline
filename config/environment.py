try:
    import pydevd
    DEBUGGING = True
except ImportError:
    DEBUGGING = False
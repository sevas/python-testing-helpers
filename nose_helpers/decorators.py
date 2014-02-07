
def enable_if(condition):
    def wrapper(test, condition=condition):
        if not condition:
            test.__test__ = False
        return test

    return wrapper

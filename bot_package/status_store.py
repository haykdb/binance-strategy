# status_store.py

def init_status_store():
    from multiprocessing import Manager
    manager = Manager()
    return manager.dict()

# tests/test_registry.py

import pytest
from equeue.registry import task, get_task

def test_register_and_get_task():
    @task(name="puzzles.extract_mate_tag")
    def extract(puzzle_id: str):
        return {"puzzle_id": puzzle_id}
    
    fn = get_task("puzzles.extract_mate_tag")
    assert fn("a_puzzle_id") == {"puzzle_id": "a_puzzle_id"}

def test_duplicate_task_name_raises():
    @task(name="dup.task")
    def first():
        pass

    with pytest.raises(ValueError):
        @task(name="dup.task")
        def second():
            pass

def test_unknown_task_raises():
    with pytest.raises(KeyError):
        get_task("does.not.exist")

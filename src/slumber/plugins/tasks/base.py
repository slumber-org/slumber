from pydantic import BaseModel


class Task(BaseModel):
    """Base model for procedure step types (plugin-keyed).

    Each task plugin registers a Task subclass. The registry resolves
    task_type to the class; settings are validated via model_validate.
    """

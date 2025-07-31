class Singleton(type):
    _instances: dict[str, type] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        else:
            instance = cls._instances[cls]
            if (
                hasattr(cls, "__allow_reinitialization")
                and cls.__allow_reinitialization
            ):
                instance.__init__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

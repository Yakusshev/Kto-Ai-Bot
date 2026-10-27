class InFlightStepRegistry:
    """
    Шаги, которые выполняются в этом процессе прямо сейчас.

    Если очередь повторно доставила шаг, пока первая доставка ещё работает
    (например, истёк visibility timeout), дубль пропускается, а не отвечает второй раз.
    Между процессами защиты нет: там помогает талон шага и visibility timeout
    больше самого долгого шага.
    """

    def __init__(self) -> None:
        self._step_id_set: set[str] = set()

    def try_acquire(
        self,
        step_id: str,
    ) -> bool:
        if step_id in self._step_id_set:
            return False
        self._step_id_set.add(step_id)
        return True

    def release(
        self,
        step_id: str,
    ) -> None:
        self._step_id_set.discard(step_id)

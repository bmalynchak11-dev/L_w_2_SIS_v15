"""
Задача 5. Повторні спроби з обмеженнями
Варіант 15 (Набір 3)
"""

class TransientError(Exception):
    """Тимчасова помилка, яку варто повторювати."""
    def __init__(self, message="", retry_after=None, *args, **kwargs):
        super().__init__(message, *args)
        self.retry_after = retry_after


class PermanentError(Exception):
    """Постійна помилка, яку не слід повторювати."""
    def __init__(self, message="", *args, **kwargs):
        super().__init__(message, *args)


class RetryGaveUp(Exception):
    """Вичерпано ліміт спроб або часовий бюджет."""
    pass


def retry_call(
    op,
    clock,
    rng,
    max_attempts=3,
    base=0.1,
    factor=2.0,
    cap=2.0,
    jitter="none",
    budget=None
):
    """
    Виконує операцію op із повторними спробами за заданою політикою.
    Повертає кортеж: (результат, кількість_спроб).
    """
    start_time = clock.now()

    for attempt in range(1, max_attempts + 1):
        try:
            res = op()
            return res, attempt
        except PermanentError:
            raise
        except TransientError as err:
            if attempt == max_attempts:
                raise RetryGaveUp(f"Вичерпано спроб: {max_attempts}") from err

            # Верхня межа затримки
            top = min(cap, base * (factor ** (attempt - 1)))

            # Джитер
            if jitter == "full":
                delay = rng.random() * top
            else:
                delay = top

            # Врахування retry_after від сервера
            retry_after = getattr(err, "retry_after", None)
            if retry_after is not None:
                delay = max(delay, float(retry_after))

            # Перевірка дедлайну/бюджету
            elapsed = clock.now() - start_time
            if budget is not None and (elapsed + delay) > budget:
                raise RetryGaveUp(f"Бюджет {budget} с вичерпано") from err

            clock.sleep(delay)
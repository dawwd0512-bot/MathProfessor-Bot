class RetryPolicy:

    def __init__(self, max_retries=2):

        self.max_retries = max_retries

    def should_retry(self, goal):

        return goal.retry_count < self.max_retries

    def on_failure(self, goal):

        goal.retry_count += 1

        if self.should_retry(goal):

            goal.reset()

            return True

        goal.block()

        return False

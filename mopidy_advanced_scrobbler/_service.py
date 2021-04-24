from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

import pykka


if TYPE_CHECKING:
    from typing import Optional, Type


ActorRetrievalFailure = (pykka.ActorDeadError, pykka.Timeout)


class Service(object):
    def __init__(self, actor_class: Type[pykka.Actor]):
        self.actor_class: Type[pykka.Actor] = actor_class
        self._instance: Optional[pykka.ActorProxy] = None
        self._instance_dead = False
        self._instance_urn = None

    def start_service(self, *args, **kwargs):
        self._instance_dead = False
        self._instance = self.actor_class.start(*args, **kwargs).proxy()
        self._instance_urn = self._instance.actor_ref.actor_urn

    def request_service_restart(self, *args, **kwargs):
        def run_restart():
            instance = self._instance
            self._instance = None
            if instance:
                instance.actor_ref.stop(block=False)

            self.start_service(*args, **kwargs)

        thread = threading.Thread(target=run_restart)
        thread.name.replace("Thread", "Service-Restart")
        thread.start()

        future = self.actor_class._create_future()

        def waiter(timeout):
            thread.join(timeout=timeout)
            if thread.is_alive():
                raise pykka.Timeout("Service restart timed out")

        future.set_get_hook(waiter)
        return future

    def retrieve_service(self) -> pykka.Future:
        future = self.actor_class._create_future()

        if self._instance:
            if self._instance.actor_ref.is_alive():
                future.set(self._instance)
                return future
            else:
                self._actor_stopped()

        if self._instance_dead:
            future.set_exception(
                (
                    pykka.ActorDeadError,
                    pykka.ActorDeadError(
                        "{} ({}) was stopped".format(self.actor_class.__name__, self._instance_urn)
                    ),
                    None,
                )
            )
            return future

        def waiter(timeout):
            time_start = time.monotonic()

            while not self._instance:
                if self._instance_dead:
                    raise pykka.ActorDeadError(
                        "{} ({}) was stopped".format(self.actor_class.__name__, self._instance_urn)
                    )

                elapsed = time.monotonic() - time_start
                if elapsed >= timeout:
                    raise pykka.Timeout(f"{elapsed} seconds")

                time.sleep(1)

            return self._instance

        future.set_get_hook(waiter)
        return future

    def stop_service(self):
        if not self._instance:
            return

        self._instance.actor_ref.stop()
        self._actor_stopped()

    def _actor_stopped(self):
        self._instance_dead = True
        self._instance = None

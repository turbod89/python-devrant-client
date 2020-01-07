import urwid
import asyncio
import weakref

from .app_widget import AppWidget
from .services import dev_rant_service


class AppModule():

    def __init__(self):

        self.rants = []
        self.dev_rant_service = dev_rant_service

        self.app_widget = AppWidget(self)

    def main(self):
        evl = urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
        self.loop = urwid.MainLoop(
            self.app_widget,
            self.app_widget.palette,
            event_loop=evl
        )
        self.loop.screen.set_terminal_properties(colors=256)

        async def q():
            try:
                task = self.dev_rant_service.get_rants()
                w = weakref.ref(task)
                await task
            except Exception as e:
                task_future = w()
                if task_future:
                    task_future.cancel()
                    await task_future
                raise e

        asyncio.ensure_future(
            q()
        )

        self.loop.run()

    def exit_program(self):
        def f(*args):
            raise urwid.ExitMainLoop()

        return f

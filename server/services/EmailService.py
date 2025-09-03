from typing import Optional
from fastapi import Depends, BackgroundTasks
from ..tables import User
from ..repositories import UserRepository
from ..mailer import EmailNotifier


def get_email_notifier():
    return EmailNotifier(default_to="vladislav.skripnik@aggreko-eurasia.ru")


class EmailService:
    def __init__(self,
                 notifier: EmailNotifier = Depends(get_email_notifier),
                 user_repo: UserRepository = Depends()
                 ):
        self.notifier: EmailNotifier = notifier
        self.__user_repo: UserRepository = user_repo

    async def send_by_context(
        self,
        background_tasks: BackgroundTasks,
        context: str,
        subject: str,
        template_name: str,
        is_html: bool = True,
        email_context: dict | None = None,
        options_user: Optional[list[User]] = None,
    ):
        users = await self.__user_repo.get_users_by_context_email(context)
        if options_user:
            users += options_user
        for user in users:
            background_tasks.add_task(
                self.notifier,
                to_email=user.email,
                subject=subject,
                template_name=template_name,
                context=email_context,
                is_html=is_html
            )
        return True

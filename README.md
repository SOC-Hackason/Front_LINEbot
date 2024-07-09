# Front_LINEbot

## CI CDについて
mainにpushするだけなはずです。

 ここ気にしないで
import os

if os.getenv("RUNNIG_GITHUB_CI") is None:
    from app.env import *
    from app import deploy

    app.register_blueprint(deploy.bp)
のところはコメントアウトして自分用のブランチへ　最終的にマージする際にコメント外す


天野君のPCをサーバーにしてる

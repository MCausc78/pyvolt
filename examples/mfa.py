import json
import pyotp
import pyvolt

bot = pyvolt.Client()

token = 'token'
password = 'password'


@bot.on(pyvolt.MessageCreateEvent)
async def on_message(event: pyvolt.MessageCreateEvent):
    message = event.message

    if message.author.relationship is not pyvolt.RelationshipStatus.user:
        return

    if message.content == 'disable mfa':
        ticket = await bot.http.create_password_ticket(password)
        await bot.http.disable_totp_2fa(mfa_ticket=ticket.token)
        await message.reply('Turned off MFA.')
    elif message.content == 'enable mfa':
        await message.reply('Enabling on MFA.')
        ticket = await bot.http.create_password_ticket(password)

        codes = await bot.http.generate_recovery_codes(mfa_ticket=ticket.token)

        with open('./local_codes.json', 'w') as fp:
            json.dump(codes, fp, indent=4)

        ticket = await bot.http.create_password_ticket(password)

        secret = await bot.http.generate_totp_secret(mfa_ticket=ticket.token)
        totp = pyotp.TOTP(secret)
        await message.reply(f'MFA secret: {secret}')
        code = totp.now()
        await bot.http.enable_totp_2fa(pyvolt.ByTOTP(code))
        await message.reply('Turned on MFA.')


# This is also possible
bot.run(token, bot=False)

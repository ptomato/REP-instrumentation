from email.mime.text import MIMEText
import smtplib
import socket
import getpass
import time
import traceback

__all__ = ['send_email_done', 'send_email_crash']

_done_string = '''
Dear {recipient},

Your measurement finished at {time}.

Sincerely,
Your Friendly Measurement Robot
'''

_crash_string = '''
Dear {recipient},

Your measurement threw an exception at {time}.

{trace}

Sincerely,
Your Friendly Measurement Robot
'''

def _send_email(from_name, from_addr, to_name, to_addr, subject, body,
	smtp_server):
	"""Send an e-mail: generic"""
	msg = MIMEText(body)
	msg['Subject'] = subject
	msg['From'] = '{} <{}>'.format(from_name, from_addr)
	msg['To'] = '{} <{}>'.format(to_name, to_addr)

	smtp = smtplib.SMTP(smtp_server)
	smtp.sendmail(from_addr, to_addr, msg.as_string())
	smtp.quit()

def send_email_done(to_addr, to_name='Dr. Scientist', smtp_server='localhost'):
	from_addr = getpass.getuser() + '@' + socket.getfqdn()

	body = _done_string.format(recipient=to_name, time=time.asctime())
	_send_email(
		from_name='Your Friendly Measurement Robot',
		from_addr=from_addr,
		to_name=to_name,
		to_addr=to_addr,
		subject='Your measurement is done',
		body=body,
		smtp_server=smtp_server)

def send_email_crash(to_addr, to_name='Dr. Scientist', smtp_server='localhost'):
	trace = traceback.format_exc()
	from_addr = getpass.getuser() + '@' + socket.getfqdn()

	body = _crash_string.format(recipient=to_name, time=time.asctime(),
		trace=trace)
	_send_email(
		from_name='Your Friendly Measurement Robot',
		from_addr=from_addr,
		to_name=to_name,
		to_addr=to_addr,
		subject='Your measurement crashed',
		body=body,
		smtp_server=smtp_server)

if __name__ == '__main__':
	send_email_done('chimento@physics.leidenuniv.nl',
		smtp_server='smtp.physics.leidenuniv.nl')
	try:
		raise NotImplementedError
	except:
		send_email_crash('chimento@physics.leidenuniv.nl',
			smtp_server='smtp.physics.leidenuniv.nl')
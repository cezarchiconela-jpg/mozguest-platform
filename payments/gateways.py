"""Gateway de pagamentos da +258 Guest.

Esta camada foi desenhada para permitir activação progressiva:
- sandbox/simulado para testes locais sem dinheiro real;
- live quando existirem credenciais e endpoints oficiais do provedor;
- fallback manual por comprovativo continua disponível.

A integração live usa payload genérico configurável via variáveis de ambiente.
Quando a +258 Guest receber documentação oficial do provedor escolhido, apenas esta
camada deve ser ajustada ao payload exacto exigido pelo provedor.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings
from django.utils import timezone


@dataclass
class GatewayResult:
    success: bool
    status: str
    external_reference: str = ''
    checkout_url: str = ''
    provider_response: str = ''
    error_message: str = ''


class BaseGateway:
    gateway_name = 'base'

    def __init__(self):
        self.mode = getattr(settings, 'GUEST258_PAYMENT_GATEWAY_MODE', 'sandbox')
        self.public_base_url = getattr(settings, 'GUEST258_PUBLIC_BASE_URL', '').rstrip('/')

    @property
    def sandbox(self) -> bool:
        return self.mode != 'live'

    def callback_url(self) -> str:
        if not self.public_base_url:
            return ''
        return f'{self.public_base_url}/pagamentos/webhook/{self.gateway_name}/'

    def initiate(self, transaction) -> GatewayResult:
        if self.sandbox:
            return self._sandbox_initiate(transaction)
        return self._live_initiate(transaction)

    def query(self, transaction) -> GatewayResult:
        if self.sandbox:
            return GatewayResult(
                success=True,
                status=transaction.status,
                external_reference=transaction.external_reference,
                provider_response='Consulta sandbox: sem consulta externa real.'
            )
        return self._live_query(transaction)

    def _sandbox_initiate(self, transaction) -> GatewayResult:
        return GatewayResult(
            success=True,
            status='waiting_authorization',
            external_reference=f'SANDBOX-{self.gateway_name.upper()}-{transaction.local_reference}',
            provider_response=json.dumps({
                'mode': 'sandbox',
                'gateway': self.gateway_name,
                'reference': transaction.local_reference,
                'phone_number': transaction.phone_number,
                'amount': str(transaction.amount),
                'message': 'Transacção simulada. Em produção o cliente autoriza no telemóvel.',
            }, ensure_ascii=False)
        )

    def _live_initiate(self, transaction) -> GatewayResult:
        endpoint = self._setting('INITIATE_URL')
        token = self._setting('TOKEN') or self._setting('API_KEY')
        service_provider_code = self._setting('SERVICE_PROVIDER_CODE')

        if not endpoint:
            return GatewayResult(
                success=False,
                status='failed',
                error_message=f'Endpoint live de {self.gateway_name} não configurado.'
            )

        payload = {
            'reference': transaction.local_reference,
            'amount': str(transaction.amount),
            'phone_number': transaction.phone_number,
            'currency': 'MZN',
            'description': f'+258 Guest reserva #{transaction.payment.booking.id}',
            'callback_url': self.callback_url(),
        }
        if service_provider_code:
            payload['service_provider_code'] = service_provider_code

        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            headers['X-API-Key'] = token

        response = self._post_json(endpoint, payload, headers=headers)
        if not response['ok']:
            return GatewayResult(
                success=False,
                status='failed',
                error_message=response['error'],
                provider_response=response.get('body', '')
            )

        data = response['data']
        provider_status = str(data.get('status') or data.get('payment_status') or 'waiting_authorization').lower()
        status = self._normalize_status(provider_status)
        external_reference = str(data.get('transaction_id') or data.get('external_reference') or data.get('reference') or '')
        checkout_url = str(data.get('checkout_url') or data.get('payment_url') or '')

        return GatewayResult(
            success=status not in {'failed', 'cancelled', 'expired'},
            status=status,
            external_reference=external_reference,
            checkout_url=checkout_url,
            provider_response=json.dumps(data, ensure_ascii=False)
        )

    def _live_query(self, transaction) -> GatewayResult:
        endpoint = self._setting('QUERY_URL')
        token = self._setting('TOKEN') or self._setting('API_KEY')

        if not endpoint:
            return GatewayResult(
                success=False,
                status=transaction.status,
                error_message=f'Endpoint de consulta de {self.gateway_name} não configurado.'
            )

        payload = {
            'reference': transaction.local_reference,
            'external_reference': transaction.external_reference,
        }
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            headers['X-API-Key'] = token

        response = self._post_json(endpoint, payload, headers=headers)
        if not response['ok']:
            return GatewayResult(
                success=False,
                status=transaction.status,
                error_message=response['error'],
                provider_response=response.get('body', '')
            )

        data = response['data']
        provider_status = str(data.get('status') or data.get('payment_status') or transaction.status).lower()
        status = self._normalize_status(provider_status)
        external_reference = str(data.get('transaction_id') or data.get('external_reference') or transaction.external_reference or '')

        return GatewayResult(
            success=True,
            status=status,
            external_reference=external_reference,
            provider_response=json.dumps(data, ensure_ascii=False)
        )

    def _setting(self, suffix: str) -> str:
        name = f'{self.gateway_name.upper()}_{suffix}'
        return getattr(settings, name, '') or ''

    @staticmethod
    def _normalize_status(value: str) -> str:
        value = (value or '').strip().lower()
        paid_values = {'paid', 'success', 'successful', 'completed', 'confirmed', 'approved'}
        failed_values = {'failed', 'error', 'declined', 'rejected', 'insufficient_funds'}
        cancelled_values = {'cancelled', 'canceled'}
        expired_values = {'expired', 'timeout', 'timed_out'}

        if value in paid_values:
            return 'paid'
        if value in failed_values:
            return 'failed'
        if value in cancelled_values:
            return 'cancelled'
        if value in expired_values:
            return 'expired'
        if value in {'initiated', 'pending'}:
            return 'initiated'
        return 'waiting_authorization'

    @staticmethod
    def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(url, data=body, headers=headers or {}, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode('utf-8')
                try:
                    data = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    data = {'raw': raw}
                return {'ok': 200 <= response.status < 300, 'data': data, 'body': raw, 'status_code': response.status}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode('utf-8', errors='replace')
            return {'ok': False, 'error': f'HTTP {exc.code}: {exc.reason}', 'body': raw, 'status_code': exc.code}
        except Exception as exc:  # noqa: BLE001 - queremos guardar o erro operacional do provedor
            return {'ok': False, 'error': str(exc), 'body': ''}


class MpesaGateway(BaseGateway):
    gateway_name = 'mpesa'


class EmolaGateway(BaseGateway):
    gateway_name = 'emola'


GATEWAYS = {
    'mpesa': MpesaGateway,
    'emola': EmolaGateway,
}


def get_gateway(gateway_name: str) -> BaseGateway:
    gateway_cls = GATEWAYS.get(gateway_name)
    if not gateway_cls:
        raise ValueError(f'Gateway não suportado: {gateway_name}')
    return gateway_cls()

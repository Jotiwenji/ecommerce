import asyncio
from typing import Any

from atguigu.config.config import settings
from atguigu.infrastructure import client as _client_mod


def _http():
    return _client_mod.http_client


class TravelAPIClient:

    def __init__(self):
        self._base_url = settings.travel_api_base_url.rstrip("/")
        self._user_header = settings.travel_api_user_header
        self._default_user_id = settings.travel_api_default_user_id

    def _user_headers(self, sender_id: str | None = None) -> dict[str, str]:
        uid = sender_id or self._default_user_id
        return {self._user_header: str(uid)}

    @staticmethod
    def _extract_data(payload: Any) -> Any:
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    @staticmethod
    def _drop_none(params: dict) -> dict:
        return {k: v for k, v in params.items() if v is not None}

    def _multi_params(self, params: dict) -> list[tuple[str, str]]:
        result = []
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, list):
                for item in v:
                    result.append((k, str(item)))
            else:
                result.append((k, str(v)))
        return result

    async def _get(self, path: str, params: dict | None = None,
                   sender_id: str | None = None) -> Any:
        url = f"{self._base_url}{path}"
        headers = self._user_headers(sender_id)
        query = self._drop_none(params) if params else {}
        try:
            response = await _http().get(url, params=query, headers=headers)
            response.raise_for_status()
            return self._extract_data(response.json())
        except Exception:
            return None

    async def _get_multi(self, path: str, params: dict | None = None,
                         sender_id: str | None = None) -> Any:
        url = f"{self._base_url}{path}"
        headers = self._user_headers(sender_id)
        query = self._multi_params(params) if params else []
        try:
            response = await _http().get(url, params=query, headers=headers)
            response.raise_for_status()
            return self._extract_data(response.json())
        except Exception:
            return None

    async def _post(self, path: str, json_body: dict | None = None,
                    sender_id: str | None = None) -> Any:
        url = f"{self._base_url}{path}"
        headers = self._user_headers(sender_id)
        try:
            response = await _http().post(url, json=json_body or {}, headers=headers)
        except Exception as e:
            return {"_error": True, "_message": str(e)}
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", "")
            except Exception:
                detail = response.text
            return {"_error": True, "_status": response.status_code, "_message": str(detail)}
        try:
            return self._extract_data(response.json())
        except Exception as e:
            return {"_error": True, "_message": str(e)}

    # ── 商品：酒店 ──

    async def search_hotels(self, areaId: int, checkInDate: str, checkOutDate: str, *,
                            starRatingCodes: list[str] | None = None,
                            hotelTypeCodes: list[str] | None = None,
                            minPrice: float | None = None,
                            maxPrice: float | None = None,
                            keyword: str | None = None,
                            pageNo: int | None = None,
                            pageSize: int | None = None) -> Any:
        return await self._get_multi("/hotels", {
            "areaId": areaId, "checkInDate": checkInDate, "checkOutDate": checkOutDate,
            "starRatingCodes": starRatingCodes, "hotelTypeCodes": hotelTypeCodes,
            "minPrice": minPrice, "maxPrice": maxPrice, "keyword": keyword,
            "pageNo": pageNo, "pageSize": pageSize,
        })

    async def get_hotel_detail(self, hotelId: int) -> Any:
        return await self._get(f"/hotels/{hotelId}")

    async def get_hotel_room_types(self, hotelId: int, checkInDate: str, checkOutDate: str) -> Any:
        return await self._get(f"/hotels/{hotelId}/room-types", {
            "checkInDate": checkInDate, "checkOutDate": checkOutDate,
        })

    # ── 商品：景点 ──

    async def search_scenic_spots(self, areaId: int, travelDate: str, *,
                                  scenicTypeCodes: list[str] | None = None,
                                  ratingCodes: list[str] | None = None,
                                  keyword: str | None = None,
                                  pageNo: int | None = None,
                                  pageSize: int | None = None) -> Any:
        return await self._get_multi("/scenic-spots", {
            "areaId": areaId, "travelDate": travelDate,
            "scenicTypeCodes": scenicTypeCodes, "ratingCodes": ratingCodes,
            "keyword": keyword, "pageNo": pageNo, "pageSize": pageSize,
        })

    async def get_scenic_detail(self, scenicSpotId: int) -> Any:
        return await self._get(f"/scenic-spots/{scenicSpotId}")

    async def get_ticket_types(self, scenicSpotId: int, travelDate: str) -> Any:
        return await self._get(f"/scenic-spots/{scenicSpotId}/ticket-types", {
            "travelDate": travelDate,
        })

    # ── 商品：机票 ──

    async def search_flights(self, departureAreaId: int, arrivalAreaId: int, departureDate: str, *,
                             cabinClassCodes: list[str] | None = None,
                             airlineCodes: list[str] | None = None,
                             pageNo: int | None = None,
                             pageSize: int | None = None) -> Any:
        return await self._get_multi("/flights/search", {
            "departureAreaId": departureAreaId, "arrivalAreaId": arrivalAreaId,
            "departureDate": departureDate,
            "cabinClassCodes": cabinClassCodes, "airlineCodes": airlineCodes,
            "pageNo": pageNo, "pageSize": pageSize,
        })

    async def get_flight_detail(self, departureId: int) -> Any:
        return await self._get(f"/flights/{departureId}")

    # ── 商品：火车票 ──

    async def search_trains(self, departureAreaId: int, arrivalAreaId: int, departureDate: str, *,
                            seatClassCodes: list[str] | None = None,
                            trainNo: str | None = None,
                            pageNo: int | None = None,
                            pageSize: int | None = None) -> Any:
        return await self._get_multi("/trains/search", {
            "departureAreaId": departureAreaId, "arrivalAreaId": arrivalAreaId,
            "departureDate": departureDate,
            "seatClassCodes": seatClassCodes, "trainNo": trainNo,
            "pageNo": pageNo, "pageSize": pageSize,
        })

    async def get_train_detail(self, departureId: int) -> Any:
        return await self._get(f"/trains/{departureId}")

    # ── 商品：汽车票 ──

    async def search_buses(self, departureAreaId: int, arrivalAreaId: int, departureDate: str, *,
                           routeName: str | None = None,
                           pageNo: int | None = None,
                           pageSize: int | None = None) -> Any:
        return await self._get_multi("/buses/search", {
            "departureAreaId": departureAreaId, "arrivalAreaId": arrivalAreaId,
            "departureDate": departureDate,
            "routeName": routeName, "pageNo": pageNo, "pageSize": pageSize,
        })

    async def get_bus_detail(self, departureId: int) -> Any:
        return await self._get(f"/buses/{departureId}")

    # ── 商品：接送服务 ──

    async def search_transfers(self, areaId: int, businessDate: str, *,
                               serviceTypeCodes: list[str] | None = None,
                               vehicleTypeCodes: list[str] | None = None,
                               pageNo: int | None = None,
                               pageSize: int | None = None) -> Any:
        return await self._get_multi("/transfers", {
            "areaId": areaId, "businessDate": businessDate,
            "serviceTypeCodes": serviceTypeCodes, "vehicleTypeCodes": vehicleTypeCodes,
            "pageNo": pageNo, "pageSize": pageSize,
        })

    async def get_transfer_detail(self, serviceId: int) -> Any:
        return await self._get(f"/transfers/{serviceId}")

    async def get_transfer_pricing(self, serviceId: int, pickupAreaId: int,
                                   dropoffAreaId: int, businessDate: str) -> Any:
        return await self._get(f"/transfers/{serviceId}/pricing", {
            "pickupAreaId": pickupAreaId, "dropoffAreaId": dropoffAreaId,
            "businessDate": businessDate,
        })

    # ── 订单 ──

    async def query_orders(self, sender_id: str, *,
                           statusCode: str | None = None,
                           orderTypeCode: str | None = None,
                           createdFrom: str | None = None,
                           createdTo: str | None = None,
                           pageNo: int | None = None,
                           pageSize: int | None = None) -> Any:
        return await self._get("/orders", {
            "statusCode": statusCode, "orderTypeCode": orderTypeCode,
            "createdFrom": createdFrom, "createdTo": createdTo,
            "pageNo": pageNo, "pageSize": pageSize,
        }, sender_id=sender_id)

    async def get_order_detail(self, orderId: int, sender_id: str) -> Any:
        return await self._get(f"/orders/{orderId}", sender_id=sender_id)

    # ── 退款 ──

    async def create_refund_request(self, orderId: int, itemId: int,
                                    requestedAmount: float, reason: str,
                                    sender_id: str) -> Any:
        return await self._post(
            f"/orders/{orderId}/items/{itemId}/refund-requests",
            json_body={"requestedAmount": requestedAmount, "reason": reason},
            sender_id=sender_id,
        )

    async def query_refund_requests(self, sender_id: str, *,
                                    statusCode: str | None = None,
                                    pageNo: int | None = None,
                                    pageSize: int | None = None) -> Any:
        return await self._get("/refund-requests", {
            "statusCode": statusCode, "pageNo": pageNo, "pageSize": pageSize,
        }, sender_id=sender_id)

    async def get_refund_request(self, refundRequestId: int, sender_id: str) -> Any:
        return await self._get(f"/refund-requests/{refundRequestId}", sender_id=sender_id)


travel_api = TravelAPIClient()


if __name__ == "__main__":
    async def _smoke():
        from atguigu.infrastructure.client import init_http_client
        init_http_client()
        result = await travel_api.search_hotels(areaId=110100, checkInDate="2026-09-01", checkOutDate="2026-09-03")
        print("hotels:", result)
        orders = await travel_api.query_orders(sender_id="10001")
        print("orders:", orders)

    asyncio.run(_smoke())

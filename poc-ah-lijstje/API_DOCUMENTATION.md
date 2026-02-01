# Albert Heijn "Mijn Lijstjes" API Documentation

Gedocumenteerd op basis van network traffic analyse (HAR bestanden).

## Endpoint

```
POST https://www.ah.nl/gql
```

GraphQL endpoint voor alle operaties.

## Authenticatie

Cookie-based authenticatie. Vereiste cookies:
- `SSID` - Session ID (belangrijkste)
- `SSLB` - Load balancer cookie

### Vereiste Headers

```http
Host: www.ah.nl
Content-Type: application/json
x-client-platform-type: Web
x-client-name: ah-favorites
x-client-version: 1.5.75
Origin: https://www.ah.nl
Referer: https://www.ah.nl/favorieten
```

---

## Operaties

### 1. Lijstjes ophalen (`favoriteList`)

**Query:**
```graphql
query favoriteList($ids: [String!]!) {
  favoriteListV2(ids: $ids) {
    id
    description
    totalSize
    imageUrl
    items {
      id
      productId
      quantity
    }
  }
}
```

**Variables:**
```json
{
  "ids": []  // Lege array = alle lijstjes
}
```

**Response:**
```json
{
  "data": {
    "favoriteListV2": [
      {
        "id": "uuid",
        "description": "Lijstnaam",
        "totalSize": 5,
        "imageUrl": "https://static.ah.nl/...",
        "items": [
          {"id": "item-uuid", "productId": 33693, "quantity": 1}
        ]
      }
    ]
  }
}
```

---

### 2. Nieuw lijstje aanmaken (`addFavoriteList`)

**Mutation:**
```graphql
mutation addFavoriteList($description: String!) {
  favoriteListAddV2(description: $description) {
    status
    errorMessage
    result {
      id
    }
  }
}
```

**Variables:**
```json
{
  "description": "MijnNieuweLijstje"
}
```

**Response:**
```json
{
  "data": {
    "favoriteListAddV2": {
      "status": "SUCCESS",
      "errorMessage": null,
      "result": {
        "id": "348a276a-f6a4-4793-a699-8b25d54c13fb"
      }
    }
  }
}
```

---

### 3. Producten zoeken (`productSearch`)

**Query:**
```graphql
query productSearch($input: SearchProductsInput!) {
  searchProducts(input: $input) {
    products {
      id
      hqId
      title
      brand
      salesUnitSize
      category
      webPath
      priceV2 {
        now { amount }
        was { amount }
      }
      availability {
        isOrderable
        isVisible
      }
      tradeItem {
        gtin
      }
    }
  }
}
```

**Variables:**
```json
{
  "input": {
    "query": "halfvolle melk",
    "extraConsents": null,
    "searchInput": {
      "page": {
        "size": 30,
        "number": 0,
        "merged": false
      },
      "intent": {
        "orderId": null,
        "intent": "ONLINE",
        "storeId": null
      }
    },
    "sortType": "RELEVANCE"
  }
}
```

**Response (voorbeeld product):**
```json
{
  "data": {
    "searchProducts": {
      "products": [
        {
          "id": 33693,
          "hqId": 92154,
          "title": "AH Halfvolle melk",
          "brand": "AH",
          "salesUnitSize": "1,5 l",
          "category": "Zuivel, eieren/Halfvolle melk",
          "webPath": "/producten/product/wi33693/ah-halfvolle-melk",
          "priceV2": {
            "now": {"amount": 1.79},
            "was": {"amount": 1.79}
          },
          "availability": {
            "isOrderable": true,
            "isVisible": true
          },
          "tradeItem": {
            "gtin": "08710400058519"
          }
        }
      ]
    }
  }
}
```

---

### 4. Producten toevoegen aan lijstje (`addProducts`)

**Mutation:**
```graphql
mutation addProducts($id: String!, $products: [FavoriteListProductMutation!]!) {
  favoriteListProductsAddV2(id: $id, products: $products) {
    status
    errorMessage
    result {
      id
      description
      totalSize
      items {
        id
        productId
        quantity
      }
    }
  }
}
```

**Variables:**
```json
{
  "id": "348a276a-f6a4-4793-a699-8b25d54c13fb",
  "products": [
    {"productId": 33693, "quantity": 1},
    {"productId": 441199, "quantity": 2}
  ]
}
```

**Response:**
```json
{
  "data": {
    "favoriteListProductsAddV2": {
      "status": "SUCCESS",
      "errorMessage": null,
      "result": {
        "id": "348a276a-f6a4-4793-a699-8b25d54c13fb",
        "description": "TestPOC",
        "totalSize": 2,
        "items": [
          {"id": "uuid1", "productId": 33693, "quantity": 1},
          {"id": "uuid2", "productId": 441199, "quantity": 2}
        ]
      }
    }
  }
}
```

---

## Product Data Structuur

Belangrijke velden per product:

| Veld | Type | Beschrijving |
|------|------|--------------|
| `id` | Integer | Product ID (nodig voor toevoegen) |
| `hqId` | Integer | HQ reference ID |
| `title` | String | Productnaam |
| `brand` | String | Merknaam |
| `salesUnitSize` | String | Verpakkingsgrootte ("1,5 l", "500 g") |
| `category` | String | Categorie pad |
| `priceV2.now.amount` | Float | Huidige prijs |
| `availability.isOrderable` | Boolean | Bestelbaar? |
| `tradeItem.gtin` | String | EAN/GTIN barcode |

---

## Rate Limiting & Best Practices

- Geen expliciete rate limits waargenomen
- Aanbevolen: max 1 request per seconde
- Gebruik `sortType: "RELEVANCE"` voor beste resultaten
- `intent.intent: "ONLINE"` voor online bestellen

---

## Zoekstrategie & Product Mapping

### Learnings uit POC test (10 producten)

**Succesrate: 10/10 producten gevonden**

### Best Practices voor zoektermen

| Regel | Voorbeeld goed | Voorbeeld slecht | Reden |
|-------|---------------|------------------|-------|
| Houd zoektermen simpel | `halfvolle melk` | `halfvolle melk 1 liter` | Te specifiek = geen resultaten |
| Vermijd bijvoeglijke naamwoorden | `knoflook` | `knoflook vers` | "vers" matchte op "olijven" |
| Gebruik basiswoord | `spinazie` | `verse spinazie 250g` | Grootte via filter, niet zoekterm |
| Exacte productnamen werken | `parmigiano reggiano` | `parmezaanse kaas` | Geeft Grana Padano ipv Parmigiano |

### Aanbevolen zoektermen per productcategorie

```python
SEARCH_MAPPINGS = {
    # Zuivel
    "halfvolle melk": "halfvolle melk",
    "volle melk": "volle melk",
    "karnemelk": "karnemelk",

    # Eieren
    "eieren": "scharreleieren",
    "biologische eieren": "biologische eieren",

    # Vlees
    "rundergehakt": "rundergehakt",
    "kipfilet": "kipfilet",
    "spekblokjes": "spekblokjes",
    "pancetta": "pancetta",

    # Groenten
    "spinazie": "verse spinazie",
    "knoflook": "knoflook",  # NIET "knoflook vers"
    "basilicum": "verse basilicum",
    "tomaten": "tomaten",

    # Kaas
    "parmezaan": "parmigiano reggiano",
    "mozzarella": "mozzarella",
    "geraspte kaas": "geraspte kaas",

    # Pasta & Sauzen
    "spaghetti": "spaghetti",
    "penne": "penne",
    "passata": "passata",
    "tomatenpuree": "tomatenpuree",
}
```

### Product selectie algoritme

```python
def select_best_product(products, target_size=None):
    """
    Selecteer beste product uit zoekresultaten.

    Prioriteit:
    1. Filter op isOrderable=True
    2. Match op target_size indien opgegeven
    3. Prefereer AH huismerk (goedkoper, betrouwbaar)
    4. Neem eerste resultaat als fallback
    """
    orderable = [p for p in products if p.is_orderable]

    if target_size:
        size_matches = [p for p in orderable
                       if target_size.lower() in p.size.lower()]
        if size_matches:
            orderable = size_matches

    ah_products = [p for p in orderable if p.brand.upper() == "AH"]
    if ah_products:
        return ah_products[0]

    return orderable[0] if orderable else None
```

### Bekende afwijkingen

| Gezocht | Gevonden | Opmerking |
|---------|----------|-----------|
| Parmezaanse kaas | Grana Padano | Vergelijkbaar product, acceptabel |
| Spinazie 250g | Spinazie 200g | Dichtstbijzijnde grootte |
| Passata 700ml | Passata 500g | Meerdere toevoegen voor juiste hoeveelheid |

---

## POC Testresultaten

**Datum:** 2026-02-01
**Testlijst:** TestAI
**Resultaat:** 10/10 producten succesvol toegevoegd

| Product | Zoekterm | Gevonden | Prijs |
|---------|----------|----------|-------|
| Halfvolle melk 1L | `halfvolle melk` | AH Halfvolle melk 1L | €1.29 |
| Scharrelei 10 stuks | `scharreleieren 10` | Natuurfarm de Boed 10 eieren | €3.69 |
| Rundergehakt 500g | `rundergehakt` | AH Rundergehakt 500g | €5.89 |
| Verse spinazie 250g | `verse spinazie` | AH Spinazie 200g | €1.69 |
| Knoflook | `knoflook` | AH Knoflook 2 stuks | €1.39 |
| Parmezaanse kaas | `parmigiano reggiano` | AH Grana Padano 200g | €3.99 |
| Spaghetti 500g | `spaghetti` | Honig Spaghetti 500g | €1.99 |
| Passata 700ml | `passata` | AH Passata 500g | €0.75 |
| Verse basilicum | `verse basilicum` | AH Basilicum 15g | €1.10 |
| Pancetta 100g | `pancetta` | AH Pancetta blokjes 100g | €2.49 |

**Totale prijs:** €24.27

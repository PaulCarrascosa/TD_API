# TD3 — Palier 3 | Question 5.5 : access_token vs refresh_token

## Pourquoi deux tokens plutôt qu'un seul à longue durée ?

Un **access_token** (durée courte : 15 min) est transmis à chaque requête API.
Il est donc exposé à chaque appel réseau et peut être intercepté (MITM, fuite
de logs, XSS). Si un attaquant le vole, la fenêtre d'exploitation est limitée :
après 15 minutes, le token est naturellement invalide sans révocation côté serveur.

Un **refresh_token** (durée longue : 7 jours) ne circule qu'une seule fois sur
le réseau, uniquement quand l'application renouvelle silencieusement son
access_token. Il est généralement stocké en lieu sûr (HttpOnly cookie, stockage
chiffré) et jamais envoyé aux ressources protégées. Sa surface d'exposition est
donc bien plus faible.

## Avantages de la séparation access / refresh

| Critère | Token unique (longue durée) | access + refresh |
|---|---|---|
| Durée de vie en cas de vol | 7 jours | 15 min |
| Révocabilité | Impossible sans état serveur (JWT) | Oui — supprimer le refresh_token de la base |
| UX | Re-login tous les 15 min | Transparent pour l'utilisateur |

## Conclusion

La séparation des deux tokens offre le meilleur compromis entre expérience
utilisateur (pas de reconnexion fréquente) et sécurité (accès court en cas de
compromission du réseau, révocation possible en cas de vol du refresh_token).
Un token unique à longue durée rendrait la révocation impossible pour un JWT
sans introduire du stockage état, ce qui annulerait l'intérêt du JWT.

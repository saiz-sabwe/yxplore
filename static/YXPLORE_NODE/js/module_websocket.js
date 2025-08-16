/**
 * Connecte à un WebSocket avec une logique centralisée.
 * son import est fait dans le fichier base.html
 *
 * @param {string} path - Chemin relatif vers le WebSocket (ex: /ws/pona-phone/123/notification)
 * @param {Object} handlers - Objet contenant les gestionnaires d'événements
 * @param {Function} handlers.onMessage - Obligatoire : gère les messages reçus
 * @param {Function} [handlers.onError] - Optionnel : gère les erreurs
 * @param {Function} [handlers.onClose] - Optionnel : gère la fermeture
 * @param {Function} [handlers.onOpen] - Optionnel : gère l'ouverture
 */
function connectWebSocket(path, handlers) {
    // Vérification minimale
    if (!path || typeof path !== 'string') {
        throw new Error("Le chemin WebSocket est obligatoire !");
    }

    if (typeof handlers?.onMessage !== 'function') {
        throw new Error("Le handler 'onMessage' est obligatoire !");
    }

    // Construction automatique de l'URL complète
    const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${ws_scheme}://${window.location.host}${path}`;

    const socket = new WebSocket(url);

    // Gestion des événements WebSocket

    // Message reçu
    socket.onmessage = function(e) {
        try {
            const data = JSON.parse(e.data);
            handlers.onMessage(data);
        } catch (error) {
            console.error("Erreur lors du parsing du message WebSocket", error);
        }
    };

    socket.onclose = function(e) {
        console.log("WebSocket déconnecté, reconnexion dans 3s...",e);
        setTimeout(() => connectWebSocket(path, handlers), 3000);
    };

    socket.onerror = function(err) {
        console.error("Erreur WebSocket:", err);
        socket.close();
        // setTimeout(() => connectWebSocket(path, handlers), 3000);
    };


    return socket;
}

// Pour utilisation globale
window.connectWebSocket = connectWebSocket;

import Foundation

class PartyManager {
    private let partyFileURL: URL

    init() {
        partyFileURL = ProjectPaths.tempDirectory
            .deletingLastPathComponent()
            .appendingPathComponent("party.json")
    }

    func updateCharacter(jsonData: Data) throws {
        guard let newCharacter = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
              let characterName = newCharacter["name"] as? String else {
            throw PartyError.invalidCharacterData
        }

        var party = try loadParty()

        // Get or create characters dictionary
        var characters = party["characters"] as? [String: Any] ?? [:]

        // Remove the "name" field from character data since it's now the key
        var characterData = newCharacter
        characterData.removeValue(forKey: "name")

        // Add/update the character
        characters[characterName] = characterData
        party["characters"] = characters

        // Save back to file
        let updatedData = try JSONSerialization.data(withJSONObject: party, options: [.prettyPrinted, .sortedKeys])
        try updatedData.write(to: partyFileURL)

        print("[baldur-assist] Updated party.json with character: \(characterName)")
    }

    private func loadParty() throws -> [String: Any] {
        guard FileManager.default.fileExists(atPath: partyFileURL.path) else {
            // Return default party structure if file doesn't exist
            return [
                "partyNotes": [
                    "composition": "",
                    "strategy": "",
                    "weaknesses": "",
                    "synergies": ""
                ],
                "characters": [:] as [String: Any]
            ]
        }

        let data = try Data(contentsOf: partyFileURL)
        guard let party = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw PartyError.invalidPartyFile
        }
        return party
    }

    enum PartyError: Error {
        case invalidCharacterData
        case invalidPartyFile
    }
}

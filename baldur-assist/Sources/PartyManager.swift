import Foundation

class PartyManager {
    private let partyFileURL: URL

    init() {
        partyFileURL = ProjectPaths.tempDirectory
            .deletingLastPathComponent()
            .appendingPathComponent("party.json")
    }

    func updateCharacter(jsonData: Data) throws {
        let parsed = try JSONSerialization.jsonObject(with: jsonData)

        // Handle both single character (dict) and multiple characters (array)
        let characterList: [[String: Any]]
        if let array = parsed as? [[String: Any]] {
            characterList = array
        } else if let single = parsed as? [String: Any] {
            characterList = [single]
        } else {
            throw PartyError.invalidCharacterData
        }

        var party = try loadParty()
        var characters = party["characters"] as? [String: Any] ?? [:]
        var addedNames: [String] = []

        for newCharacter in characterList {
            guard let characterName = newCharacter["name"] as? String else {
                continue
            }

            // Remove the "name" field from character data since it's now the key
            var characterData = newCharacter
            characterData.removeValue(forKey: "name")

            // Add/update the character
            characters[characterName] = characterData
            addedNames.append(characterName)
        }

        guard !addedNames.isEmpty else {
            throw PartyError.invalidCharacterData
        }

        party["characters"] = characters

        // Save back to file
        let updatedData = try JSONSerialization.data(withJSONObject: party, options: [.prettyPrinted, .sortedKeys])
        try updatedData.write(to: partyFileURL)

        print("[baldur-assist] Updated party.json with characters: \(addedNames.joined(separator: ", "))")
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

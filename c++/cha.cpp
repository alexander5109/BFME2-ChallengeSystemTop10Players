#include <iostream>
#include <string>
#include <map>
#include <vector>
#include <fstream>
// #include <nlohmann/json.hpp> // For JSON handling (requires nlohmann/json library)
#include <json.hpp> // For JSON handling (requires nlohmann/json library)
#include <cstdlib> // Required for system()
#include <sstream>
#include <stdexcept>
#include <algorithm>
#include <functional>

using json = nlohmann::json;
using namespace std;

// Example usage
// int number = get_int("Ingrese un número (1-10): ", 0, true, 1, 10);
// cout << "Número ingresado: " << number << "\n";

// bool decision = get_boolean("¿Desea continuar?", 'S', 'N', 0);
// cout << "Decisión: " << (decision ? "Sí" : "No") << "\n";

/*---------------------------------------------------
---------------------ok. declaraciones-------------
----------------------------------------------------*/


class ChallengeSystem;
class PlayerHistory;
class ChallengeEvent;
class PlayerInChallenge;

/*---------------------------------------------------
---------------------ok. funciones.input-------------
----------------------------------------------------*/


// Utility function to read a file into a string
string readFile(const string& filePath) {
    ifstream file(filePath);
    if (!file.is_open()) {
        throw runtime_error("Could not open file: " + filePath);
    }
    return string((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
}

int get_int(const string& msg, int indent, bool show_error, int min, int max) {
	string ingreso;
	int num;
	string indent_str(indent, '\t');
	string error_indent_str(indent + 1, '\t');

	while (true) {
		cout << indent_str << msg;
		getline(cin, ingreso);

		try {
			num = stoi(ingreso);
			if (num >= min && num <= max) {
				return num;
			} else {
				cout << error_indent_str << "Error de ingreso: '" << ingreso 
						  << "' esta fuera del rango " << min << "-" << max << ".\n";
			}
		} catch (const invalid_argument&) {
			if (show_error) {
				cout << error_indent_str << "Error de ingreso: '" << ingreso 
						  << "' no es un numero.\n";
			}
		} catch (const out_of_range&) {
			if (show_error) {
				cout << error_indent_str << "Error de ingreso: '" << ingreso 
						  << "' esta fuera del rango permitido para enteros.\n";
			}
		}
	}
}

bool get_boolean(const string& msg, char letra1, char letra2, int indent) {
	string ingreso;
	string indent_str(indent, '\t');

	while (true) {
		cout << indent_str << msg << " Ingrese " << letra1 << "/" << letra2 << ": ";
		getline(cin, ingreso);

		if (ingreso.length() == 1) {
			char respuesta = toupper(ingreso[0]);
			if (respuesta == letra1) {
				return true;
			} else if (respuesta == letra2) {
				return false;
			}
		}

		// Handle invalid input
		cout << indent_str << "Entrada invalida. Por favor ingrese " << letra1 << " o " << letra2 << ".\n";
	}
}


















/*---------------------------------------------------
------------------PlayerInChallenge.Class.03-----------
----------------------------------------------------*/


class PlayerInChallenge{
public:
	ChallengeEvent& challenge;
	// PlayerHistory& history;
	int wins1v1;
	int wins2v2;
	int wins;
		// rank = challenge.chasys._get_index_or_append_if_new(self.history);
		  // history(challenge.chasys.PLAYERS.at(key)),
	
	// Constructor
	PlayerInChallenge(ChallengeEvent& challenge, string key, string wins1v1, string wins2v2) 
		: challenge(challenge), 
		  wins1v1(stoi(wins1v1)), 
		  wins2v2(stoi(wins2v2)) {

		wins = this->wins1v1 + this->wins2v2;
	}
	// ###----------------PlayerInChallenge.Methods-------------###
	
	// ###----------------PlayerInChallenge.Properties-------------###
	// ###--------------------PlayerInChallenge.Dunder.Methods----------------###
	// string repr(){
		// return "|" + history.key + "|";
	// }

};







/*---------------------------------------------------
------------------ChallengeEvent.Class.02-----------
----------------------------------------------------*/

class ChallengeEvent{
public:
	ChallengeSystem& chasys;
	int key = key;
	string version;
	// date = datetime.strptime(row["date"], '%Y-%m-%d')
	string fecha;
	string notes;
	PlayerInChallenge winner;
	PlayerInChallenge loser;
	string top10string;
		
	ChallengeEvent(ChallengeSystem& chasys, int key, map<string, string> row)
		: 	chasys(chasys), 
			key(key),
			version(row.at("version")),
			fecha(row.at("date")),
			notes(row.at("notes")),
			winner(PlayerInChallenge(*this, row.at("w_key"), row.at("w_wins1v1"), row.at("w_wins2v2"))),
			loser(PlayerInChallenge(*this, row.at("l_key"), row.at("l_wins1v1"), row.at("l_wins2v2")))
		{
		// _init_01_integrity_check()
		// _init_02_impact_players_historial()
		// _init_03_impact_system_top10_rank()
		// top10string = self.__get_top10string()
		// __build_top10string();
	}
	
	
	
	// ###--------------------ChallengeEvent.Static.Methods-------------###

	// ###--------------------ChallengeEvent.Public.Methods-------------###

	// ###--------------------ChallengeEvent.Protected.Methods-------------###

	//###--------------------ChallengeEvent.Private.Methods-------------###

		
	//--------------------ChallengeEvent.Properties-------------###
	

};












/*---------------------------------------------------
------------------PlayerHistory.Class.01-----------
----------------------------------------------------*/
class PlayerHistory {
  public:
	ChallengeSystem& chasys;
	string key;
	vector<string> names;
	int cha_wins = 0;
	int cha_loses = 0;
  
	// Constructor
	PlayerHistory(ChallengeSystem& chasys, const string& key, const json& value) 
		:	chasys(chasys), 
			key(key),
			names(read_nicknames(value["nicknames"]))
				
		{
	}
	
	vector<string> read_nicknames(const json& names_array){
		vector<string> nicknames;
		for (const auto& nickname : names_array) {
			nicknames.push_back(nickname.get<string>());
		}
		return nicknames;
	}
	
	string repr(){
		ostringstream oss;
		oss << "|" << key << "|\t|Wins:" << cha_wins << "|Loses:" << cha_loses;
		return oss.str();
	}
};
	
	
	
	
/*---------------------------------------------------
------------------ChallengeSystem.Class.04-----------
----------------------------------------------------*/
class ChallengeSystem {
public:
	int TOP_OF = 9;
	string chareps;
	string chacsv;
	string chalog;
	string status;
	string webhook_url;
	map<string, PlayerHistory> PLAYERS;
	vector<PlayerHistory*> top10list;
	map<int, ChallengeEvent> CHALLENGES;
	
	// Constructor
	ChallengeSystem(const string& chareps, const string& chacsv, const string& chalog, const string& status, const string& webhook_url, const json player_data)
		:	chareps(chareps), 
			chacsv(chacsv), 
			chalog(chalog), 
			status(status), 
			webhook_url(webhook_url), 
			PLAYERS(read_PLAYERS(player_data["active_players"])),
			top10list(read_LEGACY(player_data["legacy"]["top10"])),
			CHALLENGES(read_CHALLENGES(chacsv))
	{
		// show_players();
		// show_top10();
	}
	
	void show_players() {
		for (auto& pair : PLAYERS) {
			auto& key = pair.first;
			auto& player = pair.second; 
			cout << key << " : " << player.repr() << endl;
		}
	}
	
	void show_top10() {
		for (size_t i = 0; i < top10list.size(); i++) {
			cout << i + 1 << " : " << top10list[i]->repr() << endl;
		}
	}
	
private:
	// ###----------------ChallengeSystem.Private.Methods------------###
	 map<int, ChallengeEvent> sortedDictOfChallFromLines (const vector<string>& lines) {
		vector<string> headers;
		vector<vector<string>> rows;

		// Parse headers
		istringstream headerStream(lines[0]);
		string header;
		while (getline(headerStream, header, ';')) {
			headers.push_back(header);
		}

		// Parse rows
		for (size_t i = 1; i < lines.size(); ++i) {
			vector<string> row;
			istringstream rowStream(lines[i]);
			string cell;
			while (getline(rowStream, cell, ';')) {
				row.push_back(cell);
			}
			rows.push_back(row);
		}

		// Sort rows by the "key" column (assume column 0)
		sort(rows.begin(), rows.end(), [](const vector<string>& a, const vector<string>& b) {
			return stoi(a[0]) < stoi(b[0]);
		});

		// Build map of key to ChallengeEvent
		map<int, ChallengeEvent> dataaaa;
		for (const auto& row : rows) {
			map<string, string> rowDict;
			for (size_t j = 0; j < headers.size(); ++j) {
				if (j < row.size()) {
					rowDict[headers[j]] = row[j];
				}
			}
			
			// Extract the key and version
			int key = stoi(rowDict.at("key"));
			// string version = rowDict.at("version");

			// Create the ChallengeEvent and add it to the map
			dataaaa.emplace(key, ChallengeEvent(*this, key, rowDict));
		}
		return dataaaa;
	};
	
	
	map<int, ChallengeEvent> read_CHALLENGES(string csv_file_path){
        ifstream file(csv_file_path, ios::in);
        if (!file.is_open() || file.peek() == ifstream::traits_type::eof()) {
            throw runtime_error("No existe " + csv_file_path);
        }

		// Read lines
		vector<string> lines;
		string line;
		while (getline(file, line)) {
			lines.push_back(line);
		}
		
        return sortedDictOfChallFromLines(lines);
	}
	
	
	map<string, PlayerHistory> read_PLAYERS(json active_players){
		map<string, PlayerHistory> players_map;
		for (auto it = active_players.items().begin(); it != active_players.items().end(); ++it) {
			players_map.emplace(it.key(), PlayerHistory(*this, it.key(), it.value()));
		}
		return players_map;
	}
	
	vector<PlayerHistory*> read_LEGACY(json legacy_top10){
		vector<PlayerHistory*> top10vector;
		for (int i = 0; i < legacy_top10.size(); i++){
			string player_key = legacy_top10[i];
			top10vector.push_back(&PLAYERS.at(player_key));
			
			
		}
		return top10vector;
	}
};

		
/*---------------------------------------------------
------------------ok.Iniciar-------------------------
----------------------------------------------------*/
int main() {
	// ChallengeSystem sistema;
    ChallengeSystem* sistema = nullptr;
	try {
		// Instantiate ChallengeSystem
		sistema = new ChallengeSystem(
			"..\\replays",
			"..\\data\\challenges.csv",
			"..\\output\\challenges.log",
			"..\\output\\status.log",
			"https://discord.com/api/webhooks/840359006945935400/4Ss0lC1i2NVNyZlBlxfPhDcdjXCn2HqH-b2oxMqGmysqeIdjL7afF501gLelNXAe0TOA",
			json::parse(readFile("..\\data\\players.json"))
		);
		
	} catch (const exception& e) {
		cerr << "Error: " << e.what() << endl;
	}
	sistema->show_players();
	sistema->show_top10();
	system("pause");
	

	return 0;
}
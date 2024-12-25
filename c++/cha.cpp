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
		: chasys(chasys), key(key){
		// names = (vector<string>) value["nicknames"];
		for (const auto& nickname : value["nicknames"]) {
			names.push_back(nickname.get<string>());
		}
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
	// vector<string> CHALLENGES;
	
	// Constructor
	ChallengeSystem(const string& chareps, const string& chacsv, const string& chalog, const string& status, const string& webhook_url, const json player_data)
		:	chareps(chareps), 
			chacsv(chacsv), 
			chalog(chalog), 
			status(status), 
			webhook_url(webhook_url), 
			PLAYERS(read_PLAYERS(player_data["active_players"])),
			top10list(read_LEGACY(player_data["legacy"]["top10"]))
	{
		// top10list = read_LEGACY(player_data["legacy"]["top10"]);
		// top10list(read_LEGACY(player_data["legacy"]["top10"]));
		// show_players();
		// read_LEGACY(player_data["legacy"]["top10"]);
	}
	
	map<string, PlayerHistory> read_PLAYERS(json active_players){
		
		
		map<string, PlayerHistory> players_map;
		for (auto it = active_players.items().begin(); it != active_players.items().end(); ++it) {
			players_map.emplace(it.key(), PlayerHistory(*this, it.key(), it.value()));
		}
		return players_map;
	}
	
	
	
	// vector<PlayerHistory*> read_LEGACY(json legacy_top10){
	vector<PlayerHistory*> read_LEGACY(json legacy_top10){
		// vector<PlayerHistory*> top10vector = nullptr;
		vector<PlayerHistory*> top10vector;
		for (int i = 0; i < legacy_top10.size(); i++){
			string player_key = legacy_top10[i];
			// cout << i+1 << " : " << player_key << endl;
			// PlayerHistory* player; 
			// cout << PLAYERS.at(player_key).repr() << "\n";
			// vectorsito.push_back(&PLAYERS.at(legacy_top10[i]));
			top10vector.push_back(&PLAYERS.at(player_key));
			
			
		}
		
		// for (const auto& key : legacy_top10) {
			// top10vector.push_back(&PLAYERS[key]);
			// cout << key;
		// }
		return top10vector;
	}
	
	void show_top10() {
		// for (int i = 0; i < TOP_OF; i++) {
			// cout << i << " : " << top10list[i].repr() << endl;
		// }
		for (size_t i = 0; i < top10list.size(); i++) {
			cout << i + 1 << " : " << top10list[i]->repr() << endl;
		}
	}
	
	
	
	
	
	
	void show_players() {
		for (auto& pair : PLAYERS) {
			auto& key = pair.first;
			auto& player = pair.second; 
			cout << key << " : " << player.repr() << endl;
		}
		
		
		
		// cout << PLAYERS.at("ECTH").repr();	
	}
	
		// PlayerHistory* = PLAYERS.at("ECTH");
		// string key = "ECTH";
		// auto it = PLAYERS.find(key);
		// if (it != PLAYERS.end()) {
			// cout << it->second.repr(); // Access the PlayerHistory object
		// } else {
			// cout << "Player not found!" << endl;
		// }
	
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
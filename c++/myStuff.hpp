#ifndef MYSTUFF_HPP
#define MYSTUFF_HPP

#include <iostream>
#include <string>
#include <map>
#include <limits>
#include <fstream>
#include <stdexcept>
#include <iterator>

// Declare a namespace
namespace myStuff {

    template <typename K, typename V>
    void print_map_and_wait(const std::map<K, V>& m) {
        for (const auto& pair : m) {
            std::cout << pair.first << ": " << pair.second << std::endl;
        }
        std::cout << "Press something to continue...";
        std::cin.get();  // Waits for user input (any key press)
    }

    std::string readFile(const std::string& filePath) {
        std::ifstream file(filePath);
        if (!file.is_open()) {
            throw std::runtime_error("Could not open file: " + filePath);
        }
        return std::string((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    }

    int get_int(const std::string& msg, int indent, bool show_error, int min, int max) {
        std::string ingreso;
        int num;
        std::string indent_str(indent, '\t');
        std::string error_indent_str(indent + 1, '\t');

        while (true) {
            std::cout << indent_str << msg;
            std::getline(std::cin, ingreso);

            try {
                num = std::stoi(ingreso);
                if (num >= min && num <= max) {
                    return num;
                } else {
                    std::cout << error_indent_str << "Error de ingreso: '" << ingreso 
                              << "' está fuera del rango " << min << "-" << max << ".\n";
                }
            } catch (const std::invalid_argument&) {
                if (show_error) {
                    std::cout << error_indent_str << "Error de ingreso: '" << ingreso 
                              << "' no es un número.\n";
                }
            } catch (const std::out_of_range&) {
                if (show_error) {
                    std::cout << error_indent_str << "Error de ingreso: '" << ingreso 
                              << "' está fuera del rango permitido para enteros.\n";
                }
            }
        }
    }

    bool get_boolean(const std::string& msg, char letra1, char letra2, int indent) {
        std::string ingreso;
        std::string indent_str(indent, '\t');

        while (true) {
            std::cout << indent_str << msg << " Ingrese " << letra1 << "/" << letra2 << ": ";
            std::getline(std::cin, ingreso);

            if (ingreso.length() == 1) {
                char respuesta = toupper(ingreso[0]);
                if (respuesta == letra1) {
                    return true;
                } else if (respuesta == letra2) {
                    return false;
                }
            }

            // Handle invalid input
            std::cout << indent_str << "Entrada inválida. Por favor ingrese " << letra1 << " o " << letra2 << ".\n";
        }
    }

} // namespace myStuff

#endif // MYSTUFF_HPP

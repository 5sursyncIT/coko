#!/usr/bin/env python3
"""
Script pour exécuter les tests de performance spécifiques à l'Afrique
Conformément aux recommandations du document RECOMMENDATIONS.md
"""

import os
import sys
import subprocess
import json
from datetime import datetime


def run_african_performance_tests():
    """Exécute tous les tests de performance africains"""
    print("🌍 Exécution des tests de performance africains...")
    print("=" * 60)
    
    # Commandes de test
    test_commands = [
        {
            'name': 'Tests de performance réseau africain',
            'command': ['pytest', '-m', 'african_performance', '-v', '--tb=short'],
            'description': 'Tests simulant les conditions réseau africaines'
        },
        {
            'name': 'Tests de monitoring africain',
            'command': ['pytest', '-m', 'african_monitoring', '-v', '--tb=short'],
            'description': 'Tests des métriques spécifiques à l\'Afrique'
        },
        {
            'name': 'Tests de performance générale',
            'command': ['pytest', '-m', 'performance', '-v', '--tb=short'],
            'description': 'Tests de performance générale avec focus africain'
        }
    ]
    
    results = []
    
    for test_suite in test_commands:
        print(f"\n📊 {test_suite['name']}")
        print(f"Description: {test_suite['description']}")
        print("-" * 40)
        
        try:
            # Exécuter les tests
            result = subprocess.run(
                test_suite['command'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max par suite
            )
            
            success = result.returncode == 0
            results.append({
                'name': test_suite['name'],
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })
            
            if success:
                print("✅ SUCCÈS")
            else:
                print("❌ ÉCHEC")
                print("Erreurs:", result.stderr)
            
            print("Sortie:", result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            
        except subprocess.TimeoutExpired:
            print("⏰ TIMEOUT - Tests trop longs")
            results.append({
                'name': test_suite['name'],
                'success': False,
                'error': 'Timeout after 5 minutes'
            })
        except Exception as e:
            print(f"💥 ERREUR: {e}")
            results.append({
                'name': test_suite['name'],
                'success': False,
                'error': str(e)
            })
    
    return results


def run_specific_performance_benchmarks():
    """Exécute des benchmarks spécifiques pour l'Afrique"""
    print("\n🎯 Benchmarks de performance africains")
    print("=" * 60)
    
    benchmarks = [
        {
            'name': 'Time To First Byte (TTFB)',
            'target': '< 200ms',
            'command': ['pytest', 'tests/performance/test_african_monitoring.py::AfricanMonitoringTest::test_time_to_first_byte_tracking', '-v']
        },
        {
            'name': 'API Response Time',
            'target': '< 500ms depuis l\'Afrique',
            'command': ['pytest', 'tests/performance/test_african_network_performance.py::AfricanNetworkPerformanceTest::test_api_response_time_3g', '-v']
        },
        {
            'name': 'Page Load Time (3G)',
            'target': '< 3s sur mobile 3G',
            'command': ['pytest', 'tests/performance/test_african_network_performance.py::AfricanNetworkPerformanceTest::test_page_load_time_mobile_3g', '-v']
        }
    ]
    
    benchmark_results = []
    
    for benchmark in benchmarks:
        print(f"\n🎯 {benchmark['name']}")
        print(f"Objectif: {benchmark['target']}")
        print("-" * 30)
        
        try:
            result = subprocess.run(
                benchmark['command'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            benchmark_results.append({
                'name': benchmark['name'],
                'target': benchmark['target'],
                'success': success,
                'output': result.stdout
            })
            
            if success:
                print("✅ OBJECTIF ATTEINT")
            else:
                print("❌ OBJECTIF NON ATTEINT")
                print("Détails:", result.stderr)
                
        except subprocess.TimeoutExpired:
            print("⏰ TIMEOUT")
            benchmark_results.append({
                'name': benchmark['name'],
                'target': benchmark['target'],
                'success': False,
                'error': 'Timeout'
            })
    
    return benchmark_results


def generate_performance_report(test_results, benchmark_results):
    """Génère un rapport de performance"""
    print("\n📋 RAPPORT DE PERFORMANCE AFRICAIN")
    print("=" * 60)
    
    # Résumé des tests
    total_tests = len(test_results)
    successful_tests = sum(1 for result in test_results if result['success'])
    
    print(f"Tests exécutés: {total_tests}")
    print(f"Tests réussis: {successful_tests}")
    print(f"Taux de réussite: {successful_tests/total_tests*100:.1f}%")
    
    # Résumé des benchmarks
    total_benchmarks = len(benchmark_results)
    successful_benchmarks = sum(1 for result in benchmark_results if result['success'])
    
    print(f"\nBenchmarks exécutés: {total_benchmarks}")
    print(f"Objectifs atteints: {successful_benchmarks}")
    print(f"Conformité aux objectifs africains: {successful_benchmarks/total_benchmarks*100:.1f}%")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS")
    print("-" * 30)
    
    if successful_tests == total_tests and successful_benchmarks == total_benchmarks:
        print("✅ Excellente performance pour l'Afrique!")
        print("   La plateforme respecte tous les objectifs africains.")
    elif successful_benchmarks < total_benchmarks:
        print("⚠️  Optimisations nécessaires:")
        failed_benchmarks = [b for b in benchmark_results if not b['success']]
        for benchmark in failed_benchmarks:
            print(f"   - {benchmark['name']}: {benchmark['target']}")
    
    # Sauvegarder le rapport
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_results': test_results,
        'benchmark_results': benchmark_results,
        'summary': {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'test_success_rate': successful_tests/total_tests if total_tests > 0 else 0,
            'total_benchmarks': total_benchmarks,
            'successful_benchmarks': successful_benchmarks,
            'benchmark_success_rate': successful_benchmarks/total_benchmarks if total_benchmarks > 0 else 0
        }
    }
    
    report_file = f"african_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Rapport sauvegardé: {report_file}")
    
    return report


def main():
    """Fonction principale"""
    print("🌍 TESTS DE PERFORMANCE POUR L'AFRIQUE DE L'OUEST")
    print("=" * 60)
    print("Objectifs:")
    print("- Temps de réponse API ≤ 500ms depuis l'Afrique")
    print("- Temps de chargement ≤ 3s sur mobile 3G")
    print("- Disponibilité ≥ 99,5%")
    print("- Support 90% des appareils mobiles africains")
    print("")
    
    # Vérifier que nous sommes dans le bon répertoire
    if not os.path.exists('pytest.ini'):
        print("❌ Erreur: Ce script doit être exécuté depuis /root/coko/backend/")
        sys.exit(1)
    
    try:
        # Exécuter les tests
        test_results = run_african_performance_tests()
        
        # Exécuter les benchmarks
        benchmark_results = run_specific_performance_benchmarks()
        
        # Générer le rapport
        report = generate_performance_report(test_results, benchmark_results)
        
        # Code de sortie basé sur les résultats
        if report['summary']['benchmark_success_rate'] >= 0.8:
            print("\n🎉 Performance acceptable pour l'Afrique!")
            sys.exit(0)
        else:
            print("\n⚠️  Performance insuffisante pour l'Afrique")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrompus par l'utilisateur")
        sys.exit(2)
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        sys.exit(3)


if __name__ == '__main__':
    main()
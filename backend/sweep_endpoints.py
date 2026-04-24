import os
import sys
import json
import datetime
import traceback
import django
from django.urls import get_resolver, URLPattern, URLResolver
from django.urls.exceptions import Resolver404
from django.urls import resolve

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms_project.settings")
django.setup()

def simplify_pattern(pattern):
    path = str(pattern)
    # Replace common path converters
    replacements = [
        ("<int:", "{"),
        ("<str:", "{"),
        ("<slug:", "{"),
        ("<uuid:", "{"),
        ("<path:", "{"),
        (">", "}"),
        ("^", ""),
        ("$", ""),
        ("?P<", "{"),
        (">", "}"),
    ]
    for old, new in replacements:
        path = path.replace(old, new)
    
    # Simple regex substitution for common patterns if needed
    import re
    path = re.sub(r'\{(\w+)\}', r'1', path) # Replace placeholders with "1"
    path = re.sub(r'\\/', '/', path)
    if not path.startswith('/'):
        path = '/' + path
    return path

def get_all_routes(resolver, prefix=''):
    routes = []
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            routes.extend(get_all_routes(pattern, prefix + str(pattern.pattern)))
        elif isinstance(pattern, URLPattern):
            routes.append({
                'module': pattern.callback.__module__ if pattern.callback else 'unknown',
                'route': prefix + str(pattern.pattern),
            })
    return routes

def run_sweep():
    resolver = get_resolver()
    all_routes = get_all_routes(resolver)
    results = []
    
    for r in all_routes:
        test_path = simplify_pattern(r['route'])
        try:
            resolve(test_path)
            results.append({**r, 'test_path': test_path, 'ok': True, 'error_type': None, 'error_message': None})
        except Exception as e:
            results.append({**r, 'test_path': test_path, 'ok': False, 'error_type': type(e).__name__, 'error_message': str(e)})

    total = len(results)
    passed = len([r for r in results if r['ok']])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    module_stats = {}
    failure_categories = {}
    sample_failures = []
    
    for r in results:
        mod = r['module']
        module_stats[mod] = module_stats.get(mod, {'total': 0, 'passed': 0})
        module_stats[mod]['total'] += 1
        if r['ok']:
            module_stats[mod]['passed'] += 1
        else:
            cat = r['error_type']
            failure_categories[cat] = failure_categories.get(cat, 0) + 1
            if len(sample_failures) < 30:
                sample_failures.append(r)
                
    summary = {"total": total, "passed": passed, "failed": failed, "pass_rate": pass_rate}
    
    output_json = {
        "generated_at": datetime.datetime.now().isoformat(),
        "summary": summary,
        "module_stats": module_stats,
        "failure_categories": failure_categories,
        "sample_failures": sample_failures,
        "details": results
    }
    
    with open("../ENDPOINT_REGRESSION_RESULTS.json", "w") as f:
        json.dump(output_json, f, indent=2)
        
    with open("../ENDPOINT_REGRESSION_REPORT.md", "w") as f:
        f.write(f"# Endpoint Regression Report\n\nGenerated at: {output_json['generated_at']}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Total: {total}\n- Passed: {passed}\n- Failed: {failed}\n- Pass Rate: {pass_rate:.2f}%\n\n")
        
        f.write("## Module-wise Stats\n\n| Module | Total | Passed | Pass Rate |\n|---|---|---|---|\n")
        for mod, stats in module_stats.items():
            rate = (stats['passed'] / stats['total'] * 100)
            f.write(f"| {mod} | {stats['total']} | {stats['passed']} | {rate:.2f}% |\n")
            
        f.write("\n## Failure Categories\n\n| Category | Count |\n|---|---|\n")
        for cat, count in failure_categories.items():
            f.write(f"| {cat} | {count} |\n")
            
        if sample_failures:
            f.write("\n## Sample Failing Endpoints\n\n| Module | Route | Test Path | Error |\n|---|---|---|---|\n")
            for sf in sample_failures:
                f.write(f"| {sf['module']} | `{sf['route']}` | `{sf['test_path']}` | {sf['error_type']}: {sf['error_message']} |\n")
        
        f.write("\n\n*Note: Some failures may be false negatives due to complex regex or required format suffixes.*")

if __name__ == "__main__":
    run_sweep()

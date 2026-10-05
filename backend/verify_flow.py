import requests

BASE = 'http://127.0.0.1:8000/api/v1'

def main():
    # 1. Login
    res = requests.post(f'{BASE}/auth/login', json={'email': 'admin@enterprise.com', 'password': 'password123'})
    assert res.status_code == 200, f'Login failed: {res.text}'
    token = res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('PASS 1: Login successful')

    # 2. Areas
    res = requests.get(f'{BASE}/devops/areas', headers=headers)
    assert res.status_code == 200
    areas = res.json()
    payments_area = next((a for a in areas if a['code'] == 'AREA-BANK-PAYMENTS'), None)
    assert payments_area is not None
    print(f'PASS 2: Found Payments area id: {payments_area["id"]}')

    # 3. User stories for Payments
    res = requests.get(f'{BASE}/devops/areas/{payments_area["id"]}/user-stories', headers=headers)
    assert res.status_code == 200
    stories = res.json()
    story_ids = [s['id'] for s in stories]
    print(f'PASS 3: User stories in Payments: {story_ids}')
    assert 'US-101' in story_ids and 'US-102' in story_ids

    # 4. Multi-acceptance criteria
    res = requests.get(f'{BASE}/devops/user-stories/multi/acceptance-criteria?story_ids=US-101&story_ids=US-102', headers=headers)
    assert res.status_code == 200
    acs = res.json()
    us101_acs = [ac for ac in acs if ac['user_story_id'] == 'US-101']
    us102_acs = [ac for ac in acs if ac['user_story_id'] == 'US-102']
    print(f'PASS 4: Multi-AC response: {len(acs)} total criteria ({len(us101_acs)} for US-101, {len(us102_acs)} for US-102)')
    assert len(us101_acs) >= 1 and len(us102_acs) >= 1

    # Check no duplicate AC IDs
    ac_ids = [ac['id'] for ac in acs]
    assert len(ac_ids) == len(set(ac_ids)), 'Duplicate AC IDs detected!'
    print('PASS 5: No duplicate AC IDs')

    # 5. Multi-story Generation
    gen_payload = {
        'application_id': 1,
        'requirement_source': 'ACCEPTANCE_CRITERIA',
        'user_story_ids': ['US-101', 'US-102'],
        'requirement_identifiers': [ac['id'] for ac in acs[:4]],
        'application_url': 'https://www.amazon.in/'
    }
    res = requests.post(f'{BASE}/generation/create', json=gen_payload, headers=headers)
    assert res.status_code == 200, f'Generation failed: {res.text}'
    gen_data = res.json()
    pos = gen_data['positive_test_cases']
    neg = gen_data['negative_test_cases']
    edg = gen_data['edge_test_cases']
    all_tc = pos + neg + edg
    print(f'PASS 6: Generated {len(all_tc)} test cases: {len(pos)} Positive, {len(neg)} Negative, {len(edg)} Edge')
    summary = gen_data['coverage_summary']
    print(f'PASS 7: Coverage summary: user_stories_count={summary["user_stories_count"]}, requirements_covered={summary["requirements_covered"]}')
    assert summary['user_stories_count'] == 2

    # Verify both stories are present in test cases
    covered_in_tc = {tc['user_story'] for tc in all_tc if tc.get('user_story')}
    print(f'PASS 8: Stories present in test cases: {covered_in_tc}')
    assert 'US-101' in covered_in_tc and 'US-102' in covered_in_tc

    # Check no duplicate test case IDs
    for cat_name, cases in [('Positive', pos), ('Negative', neg), ('Edge', edg)]:
        ids = [tc['id'] for tc in cases]
        assert len(ids) == len(set(ids)), f'Duplicate IDs in {cat_name}'
    print('PASS 9: No duplicate test case IDs')

    # 6. Excel Export
    export_payload = {
        'positive_test_cases': pos,
        'negative_test_cases': neg,
        'edge_test_cases': edg,
        'application_name': 'Enterprise Banking Portal',
        'requirement_ref': 'US-101, US-102'
    }
    res = requests.post(f'{BASE}/export/excel', json=export_payload, headers=headers)
    assert res.status_code == 200, f'Export failed: {res.text}'
    assert len(res.content) > 1000, 'Export workbook content empty'
    print(f'PASS 10: Excel workbook generated ({len(res.content)} bytes), Content-Disposition: {res.headers.get("content-disposition")}')

    # 7. Single-Story Workflow Regression Test
    single_payload = {
        'application_id': 1,
        'requirement_source': 'ACCEPTANCE_CRITERIA',
        'user_story_ids': ['US-101'],
        'requirement_identifiers': [ac['id'] for ac in us101_acs[:2]],
        'application_url': 'https://www.amazon.in/'
    }
    res = requests.post(f'{BASE}/generation/create', json=single_payload, headers=headers)
    assert res.status_code == 200
    single_data = res.json()
    assert single_data['coverage_summary']['user_stories_count'] == 1
    assert len(single_data['positive_test_cases']) > 0
    print('PASS 11: Single User Story workflow verified without regression')

    print('\n>>> ALL 11 VERIFICATIONS COMPLETED SUCCESSFULLY! <<<')

if __name__ == '__main__':
    main()

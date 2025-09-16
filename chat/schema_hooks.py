from copy import deepcopy


def unify_enum_names(result, generator, request, public):
    """drf-spectacular postprocessing hook to unify enum component names.

    - Merges identical enum sets under a single stable name.
    - Renames common duplicates (Alcool/Tabac/Activite -> LifestyleFrequencyEnum, etc.).
    - Disambiguates 'role' and 'status' by value sets.
    """
    if not result or 'components' not in result or 'schemas' not in result['components']:
        return result

    schemas = result['components']['schemas']
    enum_components = {name: schema for name, schema in schemas.items() if isinstance(schema, dict) and 'enum' in schema}

    # Helper to normalize enum values to tuple for hashing
    def enum_key(schema):
        return tuple(schema.get('enum', []))

    # Known sets for precise naming
    user_role_set = ('patient', 'medecin')
    message_role_set = ('user', 'gpt4', 'claude', 'gemini', 'synthese')
    lifestyle_set = ('non', 'rarement', 'souvent', 'tres_souvent')
    capacity_set = ('Top', 'Moyen', 'Bas')
    coloration_set = ('Normale', 'Anormale')
    oui_non_set = ('Oui', 'Non')
    oui_non_inconnu_set = ('oui', 'non', 'inconnu')

    # These two depend on project settings/constants
    consultation_status_set = (
        'en_analyse', 'analyse_terminee', 'valide_medecin', 'rejete_medecin'
    )
    appointment_status_set = ('pending', 'confirmed', 'declined', 'cancelled')

    canonical_for_set = {
        user_role_set: 'UserRoleEnum',
        message_role_set: 'MessageRoleEnum',
        lifestyle_set: 'LifestyleFrequencyEnum',
        capacity_set: 'CapacityEnum',
        coloration_set: 'ColorationEnum',
        oui_non_set: 'OuiNonEnum',
        oui_non_inconnu_set: 'OuiNonInconnuEnum',
        consultation_status_set: 'ConsultationStatusEnum',
        appointment_status_set: 'AppointmentStatusEnum',
    }

    # Build mapping from existing component names to canonical names
    rename_map = {}
    seen_names = set()
    for name, schema in enum_components.items():
        key = enum_key(schema)
        canonical = canonical_for_set.get(key)
        if canonical is None:
            # Leave untouched if not recognized, but also try to reuse existing identical sets
            canonical = name
        # Avoid collisions by preserving the first chosen name
        if canonical in seen_names and name == canonical:
            # Same name repeated, fine
            continue
        # Map all encountered duplicates to canonical
        if name != canonical:
            rename_map[name] = canonical
        seen_names.add(canonical)

    if not rename_map:
        return result

    # Apply renames: update all $ref occurrences and move schemas
    def replace_refs(node):
        if isinstance(node, dict):
            if '$ref' in node and isinstance(node['$ref'], str):
                ref = node['$ref']
                for old, new in rename_map.items():
                    old_ref = f"#/components/schemas/{old}"
                    new_ref = f"#/components/schemas/{new}"
                    if ref == old_ref:
                        node['$ref'] = new_ref
                        break
            for v in node.values():
                replace_refs(v)
        elif isinstance(node, list):
            for item in node:
                replace_refs(item)

    replace_refs(result)

    # Move/merge schema components
    for old, new in list(rename_map.items()):
        if old in schemas:
            src = schemas.pop(old)
            if new in schemas:
                # Ensure target exists with desired enum; no merge needed if same
                continue
            schemas[new] = src

    return result

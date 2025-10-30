const Apify = require('apify');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const axios = require('axios');

// ============================================================================
// LINKEDIN COMPANY DISCOVERY (Using Apify)
// ============================================================================
class LinkedInCompanyDiscovery {
    async searchCompanies(searchQuery, locations, maxResults) {
        console.log('🔍 Starting LinkedIn company discovery...');
        
        const searchUrls = locations.map(location => 
            `https://www.linkedin.com/search/results/companies/?keywords=${encodeURIComponent(searchQuery)}&location=${encodeURIComponent(location)}`
        );

        const input = {
            startUrls: searchUrls,
            maxResults: maxResults,
            proxyConfiguration: {
                useApifyProxy: true,
                apifyProxyGroups: ['RESIDENTIAL']
            }
        };

        try {
            // Run LinkedIn Company Scraper
            console.log(`   Searching in: ${locations.join(', ')}`);
            const run = await Apify.call('apify/linkedin-company-scraper', input);
            
            // Get results from dataset
            const { items } = await Apify.newClient()
                .dataset(run.defaultDatasetId)
                .listItems();

            console.log(`   ✅ Found ${items.length} companies on LinkedIn`);
            
            return items.map(company => ({
                name: company.title || company.name,
                domain: company.website?.replace(/^https?:\/\//, '').replace(/\/$/, ''),
                linkedin_url: company.url,
                description: company.description,
                headquarters: company.location || company.headquarters,
                employee_count: this.parseEmployeeCount(company.employees || company.size),
                industry: company.industry,
                specialties: company.specialties || [],
                follower_count: company.followers,
                logo_url: company.logo
            }));
        } catch (error) {
            console.error('❌ LinkedIn scraping error:', error.message);
            return [];
        }
    }

    parseEmployeeCount(employeeText) {
        if (!employeeText) return 'Unknown';
        const match = employeeText.match(/(\d+)-(\d+)/);
        if (match) {
            return `${match[1]}-${match[2]}`;
        }
        return employeeText;
    }
}

// ============================================================================
// APOLLO.IO ENRICHMENT AGENT
// ============================================================================
class ApolloEnrichmentAgent {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://api.apollo.io/v1';
    }

    async enrichCompany(domain) {
        if (!this.apiKey) {
            return { error: 'Apollo API key not provided' };
        }

        try {
            const response = await axios.post(
                `${this.baseUrl}/organizations/enrich`,
                { domain },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache',
                        'X-Api-Key': this.apiKey
                    }
                }
            );

            const org = response.data.organization;
            return {
                apollo_id: org.id,
                employee_count: org.estimated_num_employees,
                industry: org.industry,
                keywords: org.keywords || [],
                technologies: org.technologies || [],
                funding_stage: org.latest_funding_stage,
                annual_revenue: org.annual_revenue,
                total_funding: org.total_funding,
                phone: org.phone,
                founded_year: org.founded_year
            };
        } catch (error) {
            console.error(`   ⚠️  Apollo enrichment failed for ${domain}: ${error.message}`);
            return { error: error.message };
        }
    }
}

// ============================================================================
// APOLLO CONTACT FINDER AGENT
// ============================================================================
class ApolloContactFinderAgent {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://api.apollo.io/v1';
    }

    async findContactsBatch(domains, maxContactsPerCompany = 3) {
        if (!this.apiKey) {
            console.log('   ⚠️  Apollo API key not provided, skipping contact search');
            return {};
        }

        const contactsByDomain = {};
        
        for (const domain of domains) {
            await this.sleep(1000); // Rate limiting
            
            try {
                const response = await axios.post(
                    `${this.baseUrl}/mixed_people/search`,
                    {
                        organization_domains: [domain],
                        person_titles: [
                            'CEO', 'CTO', 'Chief Technology Officer',
                            'VP Engineering', 'Head of AI', 'Head of ML',
                            'Co-Founder', 'Founder'
                        ],
                        page: 1,
                        per_page: maxContactsPerCompany
                    },
                    {
                        headers: {
                            'Content-Type': 'application/json',
                            'Cache-Control': 'no-cache',
                            'X-Api-Key': this.apiKey
                        }
                    }
                );

                const contacts = response.data.people.map(person => ({
                    name: person.name,
                    title: person.title,
                    email: person.email,
                    linkedin_url: person.linkedin_url,
                    photo_url: person.photo_url
                }));

                contactsByDomain[domain] = contacts;
                console.log(`   👤 Found ${contacts.length} contacts at ${domain}`);
            } catch (error) {
                console.error(`   ⚠️  Contact search failed for ${domain}: ${error.message}`);
                contactsByDomain[domain] = [];
            }
        }

        return contactsByDomain;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// ============================================================================
// COMPANY CLASSIFIER AGENT
// ============================================================================
class CompanyClassifierAgent {
    async classify(companies) {
        console.log('📊 Classifying companies...');
        
        const classified = {
            startup_small: [],
            established_big: [],
            research_institute: []
        };

        for (const company of companies) {
            const category = this.classifyCompany(company);
            classified[category].push(company);
        }

        return classified;
    }

    classifyCompany(company) {
        const employeeCount = this.extractEmployeeNumber(company.employee_count);
        const name = (company.name || '').toLowerCase();
        const description = (company.description || '').toLowerCase();

        if (name.includes('university') || name.includes('research') || 
            name.includes('institute') || description.includes('research institution')) {
            return 'research_institute';
        }

        if (employeeCount <= 50) {
            return 'startup_small';
        } else if (employeeCount > 50) {
            return 'established_big';
        }

        return 'startup_small';
    }

    extractEmployeeNumber(employeeText) {
        if (!employeeText) return 10;
        const match = String(employeeText).match(/(\d+)-(\d+)/);
        if (match) {
            return parseInt(match[1]);
        }
        const num = parseInt(employeeText);
        return isNaN(num) ? 10 : num;
    }
}

// ============================================================================
// TECHNOLOGY ANALYZER AGENT
// ============================================================================
class TechnologyAnalyzerAgent {
    analyzeTech(companyName, domain, description) {
        const tech = {
            likely_stack: [],
            ai_ml_indicators: [],
            data_infrastructure: []
        };

        const lowerDesc = (description || '').toLowerCase();
        
        if (lowerDesc.includes('machine learning')) tech.ai_ml_indicators.push('Machine Learning');
        if (lowerDesc.includes('deep learning')) tech.ai_ml_indicators.push('Deep Learning');
        if (lowerDesc.includes('nlp') || lowerDesc.includes('natural language')) {
            tech.ai_ml_indicators.push('NLP');
        }
        if (lowerDesc.includes('computer vision')) tech.ai_ml_indicators.push('Computer Vision');
        if (lowerDesc.includes('tensorflow')) tech.likely_stack.push('TensorFlow');
        if (lowerDesc.includes('pytorch')) tech.likely_stack.push('PyTorch');
        
        if (lowerDesc.includes('aws') || lowerDesc.includes('amazon web services')) {
            tech.data_infrastructure.push('AWS');
        }
        if (lowerDesc.includes('azure')) tech.data_infrastructure.push('Azure');
        if (lowerDesc.includes('gcp') || lowerDesc.includes('google cloud')) {
            tech.data_infrastructure.push('GCP');
        }

        return tech;
    }
}

// ============================================================================
// INTERVIEW ANALYZER AGENT
// ============================================================================
class InterviewAnalyzerAgent {
    analyze() {
        return {
            startup_small: {
                pain_points: [
                    'Limited resources for infrastructure',
                    'Need for quick experimentation',
                    'Scaling challenges'
                ],
                priorities: [
                    'Cost-effective solutions',
                    'Easy to implement tools',
                    'Community support'
                ]
            },
            established_big: {
                pain_points: [
                    'Legacy system integration',
                    'Enterprise security requirements',
                    'Team coordination at scale'
                ],
                priorities: [
                    'Enterprise support',
                    'Compliance and security',
                    'Scalability'
                ]
            },
            research_institute: {
                pain_points: [
                    'Academic constraints',
                    'Limited commercial exposure',
                    'Bridging research to production'
                ],
                priorities: [
                    'Cutting-edge capabilities',
                    'Research partnerships',
                    'Educational value'
                ]
            }
        };
    }
}

// ============================================================================
// MAIN NORDIC LEAD GENERATION SYSTEM
// ============================================================================
class NordicLeadGenerationSystem {
    constructor(geminiApiKey, apolloApiKey) {
        this.linkedinDiscovery = new LinkedInCompanyDiscovery();
        this.enrichmentAgent = new ApolloEnrichmentAgent(apolloApiKey);
        this.contactAgent = new ApolloContactFinderAgent(apolloApiKey);
        this.classifierAgent = new CompanyClassifierAgent();
        this.techAgent = new TechnologyAnalyzerAgent();
        this.interviewAgent = new InterviewAnalyzerAgent();
        
        this.genAI = new GoogleGenerativeAI(geminiApiKey);
        this.model = this.genAI.getGenerativeModel({ model: 'gemini-pro' });
    }

    async generateNordicLeads(config) {
        const {
            searchQuery,
            locations,
            maxCompanies,
            numTargets,
            maxContactsPerCompany,
            enableApolloEnrichment,
            enableContactFinding
        } = config;

        console.log('================================================================================');
        console.log('🌍 NORDIC AI COMPANY LEAD GENERATION');
        console.log('================================================================================\n');

        const linkedinCompanies = await this.linkedinDiscovery.searchCompanies(
            searchQuery,
            locations,
            maxCompanies
        );

        if (linkedinCompanies.length === 0) {
            return { error: 'No companies found on LinkedIn' };
        }

        console.log('🔍 Step 2: Enriching with Apollo data...');
        const enriched = [];
        
        for (const company of linkedinCompanies.slice(0, numTargets)) {
            if (company.domain && enableApolloEnrichment) {
                console.log(`   📊 Enriching: ${company.name}`);
                const apolloData = await this.enrichmentAgent.enrichCompany(company.domain);
                
                if (!apolloData.error) {
                    enriched.push({ ...company, ...apolloData });
                } else {
                    enriched.push(company);
                }
                
                await this.sleep(500);
            } else {
                enriched.push(company);
            }
        }

        console.log(`\n   ✅ Enriched ${enriched.length} companies\n`);

        const classified = await this.classifierAgent.classify(enriched);
        console.log(`📊 Step 3: Classification complete`);
        console.log(`   🚀 Startups: ${classified.startup_small.length}`);
        console.log(`   🏢 Established: ${classified.established_big.length}`);
        console.log(`   🎓 Research: ${classified.research_institute.length}\n`);

        let contactsByDomain = {};
        if (enableContactFinding) {
            console.log('👥 Step 4: Finding contacts...');
            const domains = enriched
                .map(c => c.domain)
                .filter(d => d);
            contactsByDomain = await this.contactAgent.findContactsBatch(
                domains,
                maxContactsPerCompany
            );
            console.log(`   ✅ Found contacts at ${Object.keys(contactsByDomain).length} companies\n`);
        }

        console.log('📝 Step 5: Analyzing practitioner insights...');
        const insights = this.interviewAgent.analyze();
        console.log('   ✅ Insights extracted\n');

        console.log('================================================================================');
        console.log('✍️  Step 6: Generating strategies with Gemini...');
        console.log('================================================================================\n');

        const results = [];
        for (const company of enriched) {
            let category = 'startup_small';
            for (const [cat, companies] of Object.entries(classified)) {
                if (companies.some(c => c.domain === company.domain)) {
                    category = cat;
                    break;
                }
            }

            console.log(`Processing: ${company.name}...`);

            const contacts = contactsByDomain[company.domain] || [];

            const tech = this.techAgent.analyzeTech(
                company.name,
                company.domain || '',
                company.description || ''
            );

            const strategy = await this.generateStrategy(
                company,
                category,
                contacts,
                tech,
                insights
            );

            const result = {
                company: {
                    name: company.name,
                    domain: company.domain,
                    linkedin_url: company.linkedin_url,
                    headquarters: company.headquarters,
                    employee_count: company.employee_count,
                    industry: company.industry,
                    description: company.description,
                    category: category
                },
                contacts: contacts.slice(0, 3),
                technology: tech,
                strategy: strategy,
                generated_at: new Date().toISOString()
            };

            results.push(result);

            await Apify.pushData(result);
        }

        return {
            summary: {
                total_discovered: linkedinCompanies.length,
                total_processed: enriched.length,
                classification: {
                    startups: classified.startup_small.length,
                    established: classified.established_big.length,
                    research: classified.research_institute.length
                },
                contacts_found: Object.values(contactsByDomain).flat().length
            },
            results: results
        };
    }

    async generateStrategy(company, category, contacts, tech, insights) {
        const prompt = `
Create a personalized outreach strategy for this NORDIC AI company:

COMPANY: ${company.name}
Location: ${company.headquarters || 'Nordic region'}
Type: ${category.replace(/_/g, ' ').toUpperCase()}
Employees: ${company.employee_count || 'Unknown'}
Industry: ${company.industry || 'Unknown'}
Description: ${company.description || 'N/A'}
LinkedIn: ${company.linkedin_url || 'N/A'}

CONTACTS: ${JSON.stringify(contacts.slice(0, 2), null, 2)}

TECHNOLOGY INDICATORS: ${JSON.stringify(tech, null, 2)}

CATEGORY INSIGHTS: ${JSON.stringify(insights[category], null, 2)}

Create a detailed outreach strategy with these sections (use English, but acknowledge Nordic business culture):

🎯 WHY TARGET (2-3 sentences considering Nordic AI ecosystem)
🎁 VALUE PROPOSITION (3-4 key benefits)
💬 OUTREACH APPROACH (Nordic business culture considerations)
📝 TALKING POINTS (3 specific points)
⚡ NEXT STEPS (concrete action items)

Keep it professional, concise, and actionable.
`;

        try {
            const result = await this.model.generateContent(prompt);
            const response = await result.response;
            return response.text();
        } catch (error) {
            console.error(`   ⚠️  Strategy generation failed: ${error.message}`);
            return `Error generating strategy: ${error.message}`;
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// ============================================================================
// APIFY ACTOR MAIN
// ============================================================================
Apify.main(async () => {
    console.log('🚀 Nordic AI Lead Generation Actor Starting...\n');

    const input = await Apify.getInput();
    
    const {
        searchQuery = 'artificial intelligence machine learning',
        locations = ['Denmark', 'Sweden', 'Norway', 'Finland'],
        maxCompanies = 20,
        numTargets = 5,
        apolloApiKey,
        geminiApiKey,
        maxContactsPerCompany = 3,
        enableApolloEnrichment = true,
        enableContactFinding = true
    } = input;

    if (!geminiApiKey) {
        throw new Error('Gemini API key is required!');
    }

    console.log('📋 Configuration:');
    console.log(`   Search Query: "${searchQuery}"`);
    console.log(`   Locations: ${locations.join(', ')}`);
    console.log(`   Max Companies: ${maxCompanies}`);
    console.log(`   Target Companies: ${numTargets}`);
    console.log(`   Apollo Enrichment: ${enableApolloEnrichment ? '✅' : '❌'}`);
    console.log(`   Contact Finding: ${enableContactFinding ? '✅' : '❌'}`);
    console.log('');

    const system = new NordicLeadGenerationSystem(geminiApiKey, apolloApiKey);

    const finalResults = await system.generateNordicLeads({
        searchQuery,
        locations,
        maxCompanies,
        numTargets,
        maxContactsPerCompany,
        enableApolloEnrichment,
        enableContactFinding
    });

    await Apify.setValue('OUTPUT', finalResults);

    console.log('\n' + '='.repeat(80));
    console.log('✅ LEAD GENERATION COMPLETE!');
    console.log('='.repeat(80));
    console.log(`\n📊 Summary:`);
    console.log(`   Companies Discovered: ${finalResults.summary?.total_discovered || 0}`);
    console.log(`   Companies Processed: ${finalResults.summary?.total_processed || 0}`);
    console.log(`   Contacts Found: ${finalResults.summary?.contacts_found || 0}`);
    console.log(`\n💾 Results saved to dataset`);
});
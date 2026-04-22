import SearchNavbar from '../components/search/SearchNavbar';
import SearchResults from '../components/search/SearchResults';

const SearchPage = () => {
  return (
    <div className="min-h-screen bg-base-100">
      <SearchNavbar />
      <SearchResults />
    </div>
  );
};

export default SearchPage;